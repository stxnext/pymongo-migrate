from dataclasses import dataclass
from pathlib import Path

from pymongo_migrate.loader import load_module_migrations
from pymongo_migrate.migrations import MigrationsGraph


@dataclass
class MongoMigrate:
    mongo_uri: str  # https://docs.mongodb.com/manual/reference/connection-string/
    migrations_dir: str = "./pymongo_migrations"
    migrations_collection: str = "pymongo_migrate"

    def __post_init__(self):
        self.graph = MigrationsGraph()
        for migration in load_module_migrations(Path(self.migrations_dir)):
            self.graph.add_migration(migration)
        self.graph.verify()

    def get_state(self):
        pass

    def upgrade(self, migration_name=None):
        if migration_name and migration_name not in self.graph:
            raise ValueError(f"No such migration: {migration_name}")
        for migration in self.graph:
            if migration.name == migration_name:
                break
