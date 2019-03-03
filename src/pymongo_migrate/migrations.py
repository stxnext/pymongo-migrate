import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from types import ModuleType
from typing import Dict, List, Optional, Set

from pymongo.database import Database


@dataclass
class Migration:
    name: str
    dependencies: List[str] = field(default_factory=list)

    @property
    def initial(self):
        return not self.dependencies

    def upgrade(self, db: Database):
        raise NotImplementedError()

    def downgrade(self, db: Database):
        raise NotImplementedError()


class MigrationModuleType(ModuleType):
    """Migration Module Type stub"""

    name: str
    dependencies: List[str]

    def upgrade(self, db: Database):
        raise NotImplementedError()

    def downgrade(self, db: Database):
        raise NotImplementedError()


class MigrationModuleWrapper(Migration):
    """Use python module as a migration"""

    def __init__(self, name: str, module: MigrationModuleType):
        self.name = name
        self.module = module
        assert self.name == getattr(self.module, "name", name)
        super().__init__(name=name, dependencies=self.module.dependencies)

    @property
    def description(self):
        return self.module.__doc__

    def upgrade(self, db: Database):
        self.module.upgrade(db)

    def downgrade(self, db: Database):
        self.module.downgrade(db)


class MigrationsGraph:
    def __init__(self):
        self.migrations: Dict[str, Migration] = {}
        self.required_by: Dict[str, Set[str]] = defaultdict(set)

    def add_migration(self, migration: Migration):
        self.migrations[migration.name] = migration
        for required_migration_name in migration.dependencies:
            self.required_by[required_migration_name].add(migration.name)

    def get_initial(self):
        initial_migrations = [m for m in self.migrations.values() if m.initial]
        if len(initial_migrations) != 1:
            raise ValueError("There must be single initial migration")
        return initial_migrations[0]

    def verify(self):
        ordered_migration_names = [migration.name for migration in self]
        all_migrations = set(self.migrations.keys())
        unused_migrations = all_migrations - set(ordered_migration_names)
        if unused_migrations:
            raise ValueError("Migration graph is disconnected")

    def __iter__(self):
        """
        Iterate over migrations starting with initial one
        """
        if not self.migrations:
            return
        initial_migration = self.get_initial()
        yield from self._get_next(initial_migration)

    def _get_next(self, migration):
        yield migration
        for next_migration_name in sorted(self.required_by.get(migration.name, [])):
            next_migration = self.migrations[next_migration_name]
            yield from self._get_next(next_migration)


@dataclass
class MigrationState:
    name: str
    applied: Optional[datetime.datetime] = None
