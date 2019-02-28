import datetime
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import pymongo
from bson import CodecOptions

from pymongo_migrate.generate import generate_migration_module_in_dir
from pymongo_migrate.loader import load_module_migrations
from pymongo_migrate.migrations import Migration, MigrationsGraph

LOGGER = logging.getLogger(__name__)


def dt(*args) -> datetime:
    """Create timezone-aware UTC datetime."""
    if args:
        return datetime.datetime(*args, tzinfo=datetime.timezone.utc)
    else:
        return datetime.datetime.now(datetime.timezone.utc)


@dataclass
class MigrationStatus:
    name: str
    applied: Optional[datetime.datetime] = None

    def set_applied(self):
        self.applied = datetime.datetime.now(datetime.timezone.utc)


def _serialize(obj):
    return asdict(obj)


def _deserialize(data, cls):
    data = {**data}
    del data["_id"]
    return cls(**data)


@dataclass
class MongoMigrate:
    mongo_uri: str  # https://docs.mongodb.com/manual/reference/connection-string/
    migrations_dir: str = "./pymongo_migrations"
    migrations_collection: str = "pymongo_migrate"
    logger: logging.Logger = LOGGER

    def __post_init__(self):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.graph = MigrationsGraph()
        for migration in load_module_migrations(self.migrations_path):
            self.graph.add_migration(migration)
        self.graph.verify()

    @property
    def migrations_path(self):
        return Path(self.migrations_dir)

    @property
    def db(self):
        return self.client.get_database()

    @property
    def db_collection(self):
        return self.client.get_database()[self.migrations_collection].with_options(
            codec_options=CodecOptions(tz_aware=True, tzinfo=datetime.timezone.utc)
        )

    def get_migrations(self):
        yield from self.graph

    def get_status(self, migration: Migration) -> MigrationStatus:
        data = self.db_collection.find_one({"name": migration.name})
        if data:
            return _deserialize(data, MigrationStatus)
        return MigrationStatus(name=migration.name)

    def set_status(self, status: MigrationStatus):
        self.db_collection.replace_one(
            {"name": status.name}, _serialize(status), upsert=True
        )

    def _check_for_migration(self, migration_name: str):
        if migration_name is None:
            return None
        migration = self.graph.migrations.get(migration_name)
        if migration is None:
            raise ValueError(f"No such migration: {migration_name}")
        return migration

    def migrate(self, migration_name: Optional[str] = None):
        """
        Automatically detects if upgrades or downgrades should be applied to
        reach target migration state.

        :param migration_name:
            target migration
            None if all upgrades should be applied
        """
        if migration_name is None:
            self.logger.debug("Migration target not specified, assuming upgrade")
            self.upgrade()
        migration = self._check_for_migration(migration_name, required=True)
        migration_status = self.get_status(migration)
        if migration_status.applied:
            self.logger.debug("Migration target already applied, assuming downgrade")
            self.downgrade(migration_name)
        else:
            self.logger.debug("Migration target already applied, assuming upgrade")
            self.upgrade(migration_name)

    def upgrade(self, migration_name: Optional[str] = None):
        """
        Apply upgrade migrations.

        :param migration_name:
            name of migration up to which (including) upgrades should be executed
            None if all migrations should be run
        """
        self._check_for_migration(migration_name)
        for migration in self.graph:
            migration_status = self.get_status(migration)
            if migration_status.applied:
                LOGGER.debug("Migration %r already applied, skipping")
            LOGGER.info("Running upgrade migration %r", migration.name)
            migration.upgrade(self.db)
            migration_status.applied = dt()
            self.set_status(migration_status)
            if migration.name == migration_name:
                break

    def downgrade(self, migration_name: Optional[str]):
        """
        Reverse migrations.

        :param migration_name:
            name of migration down to which (excluding) downgrades should be executed
            None if all migrations should be run
        """
        self._check_for_migration(migration_name)
        for migration in reversed(list(self.get_migrations())):
            migration_status = self.get_status(migration)
            LOGGER.info("Running downgrade migration %r", migration.name)
            migration.downgrade(self.db)
            migration_status.applied = None
            self.set_status(migration_status)
            if migration.name == migration_name:
                break

    def generate(self, name: str = "", description: str = ""):
        last_migration_name = None
        for migration in self.get_migrations():
            last_migration_name = migration.name
        dependencies = [last_migration_name] if last_migration_name else []
        generate_migration_module_in_dir(
            self.migrations_path, name=name, description=name, dependencies=dependencies
        )
