import datetime
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Optional

import pymongo
from bson import CodecOptions

from pymongo_migrate.generate import generate_migration_module_in_dir
from pymongo_migrate.loader import load_module_migrations
from pymongo_migrate.migrations import Migration, MigrationsGraph, MigrationState

LOGGER = logging.getLogger(__name__)


def dt(*args) -> datetime.datetime:
    """Create timezone-aware UTC datetime."""
    if args:
        return datetime.datetime(*args, tzinfo=datetime.timezone.utc)  # type: ignore
    else:
        return datetime.datetime.now(datetime.timezone.utc)


def _serialize(obj):
    return asdict(obj)


def _deserialize(data, cls):
    data = {**data}
    del data["_id"]
    return cls(**data)


class _MeasureTime:
    """
    Class to measure the time of execution of code block.
    usage:

     with MeasureTime() as mt:
         # code block ...
         print(f"Execution time: {mt.elapsed}s")
    """

    def __init__(self):
        self.start = None
        self.stop = None

    @staticmethod
    def time() -> float:
        return time.time()

    @property
    def elapsed(self) -> Optional[float]:
        if self.start is None:
            return None
        return (self.stop or self.time()) - self.start

    def __enter__(self):
        self.start = self.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop = self.time()


@dataclass
class MongoMigrate:
    client: pymongo.MongoClient
    migrations_dir: str = "./pymongo_migrations"
    migrations_collection: str = "pymongo_migrate"
    logger: logging.Logger = LOGGER

    def __post_init__(self):
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

    def get_migrations(self) -> Iterator[Migration]:
        yield from self.graph

    def get_state(self, migration: Migration) -> MigrationState:
        data = self.db_collection.find_one({"name": migration.name})
        if data:
            return _deserialize(data, MigrationState)
        return MigrationState(name=migration.name)

    def set_state(self, status: MigrationState):
        self.db_collection.replace_one(
            {"name": status.name}, _serialize(status), upsert=True
        )

    def _check_for_migration(
        self, migration_name: Optional[str]
    ) -> Optional[Migration]:
        if migration_name is None:
            return None
        migration = self.graph.migrations.get(migration_name)
        if migration is None:
            raise ValueError(f"No such migration: {migration_name}")
        return migration

    def migrate(self, migration_name: Optional[str] = None, fake: bool = False):
        """
        Automatically detects if upgrades or downgrades should be applied to
        reach target migration state.

        :param migration_name:
            target migration
            None if all upgrades should be applied
        :param fake:
            If True, only migration state in database will be modified and
            no actual migration will be run.
        """
        if migration_name is None:
            self.logger.debug("Migration target not specified, assuming upgrade")
            self.upgrade(fake=fake)
            return
        migration = self._check_for_migration(migration_name)
        assert migration, "No matching migration, something went wrong"
        migration_state = self.get_state(migration)
        if migration_state.applied:
            self.logger.debug("Migration target already applied, assuming downgrade")
            self.downgrade(migration_name, fake)
        else:
            self.logger.debug("Migration target not applied, assuming upgrade")
            self.upgrade(migration_name, fake)

    def upgrade(self, migration_name: Optional[str] = None, fake: bool = False):
        """
        Apply upgrade migrations.

        :param migration_name:
            name of migration up to which (including) upgrades should be executed
            None if all migrations should be run
        :param fake:
            If True, only migration state in database will be modified and
            no actual migration will be run.
        """
        self._check_for_migration(migration_name)
        for migration in self.graph:
            migration_state = self.get_state(migration)
            if migration_state.applied:
                self.logger.debug(
                    "Migration %r already applied, skipping", migration.name
                )
                continue
            if fake:
                self.logger.info("Fake running upgrade migration %r", migration.name)
            else:
                self.logger.info("Running upgrade migration %r", migration.name)
                with _MeasureTime() as mt:
                    migration.upgrade(self.db)
                    self.logger.info(
                        "Execution time of %r: %s seconds", migration.name, mt.elapsed
                    )
            migration_state.applied = dt()
            self.set_state(migration_state)
            if migration.name == migration_name:
                break

    def downgrade(self, migration_name: Optional[str] = None, fake: bool = False):
        """
        Reverse migrations.

        :param migration_name:
            name of migration down to which (excluding) downgrades should be executed
            None if all migrations should be run
        :param fake:
            If True, only migration state in database will be modified and
            no actual migration will be run.
        """
        self._check_for_migration(migration_name)
        for migration in reversed(list(self.get_migrations())):
            if migration.name == migration_name:
                break
            migration_state = self.get_state(migration)
            if not migration_state.applied:
                self.logger.debug(
                    "Migration %r not yet applied, skipping", migration.name
                )
                continue
            if fake:
                self.logger.info("Fake running downgrade migration %r", migration.name)
            else:
                self.logger.info("Running downgrade migration %r", migration.name)
                with _MeasureTime() as mt:
                    migration.downgrade(self.db)
                    self.logger.info(
                        "Execution time of %r: %s seconds", migration.name, mt.elapsed
                    )
            migration_state.applied = None
            self.set_state(migration_state)

    def generate(self, name: str = "", **kwargs) -> Path:
        last_migration_name = None
        for migration in self.get_migrations():
            last_migration_name = migration.name
        self.migrations_path.mkdir(exist_ok=True)
        dependencies = [last_migration_name] if last_migration_name else []
        return generate_migration_module_in_dir(
            self.migrations_path,
            name=name,
            dependencies=dependencies,
            **{k: v for k, v in kwargs.items() if v is not None},
        )
