import pytest

from pymongo_migrate.migrations import Migration, MigrationState
from pymongo_migrate.mongo_migrate import dt


@pytest.fixture
def migration():
    return Migration(name="2019_test")


def test_get_state_when_migration_not_applied(mongo_migrate, db, migration):
    assert mongo_migrate.get_state(migration) == MigrationState(
        name=migration.name, applied=None
    )


def test_get_state_when_migration_not_applied_but_in_db(
    mongo_migrate, db_collection, migration
):
    db_collection.insert_one({"name": migration.name, "applied": None})
    assert mongo_migrate.get_state(migration) == MigrationState(
        name=migration.name, applied=None
    )


def test_get_state_when_migration_applied(mongo_migrate, db_collection, migration):
    now = dt().replace(microsecond=0)  # reduced time resolution
    db_collection.insert_one({"name": migration.name, "applied": now})
    assert mongo_migrate.get_state(migration) == MigrationState(
        name=migration.name, applied=now
    )


def test_set_state(mongo_migrate, db_collection, migration):
    now = dt().replace(microsecond=0)  # reduced time resolution
    mongo_migrate.set_state(MigrationState(name=migration.name, applied=now))
    all_migrations = list(db_collection.find())
    del all_migrations[0]["_id"]
    assert all_migrations == [{"name": migration.name, "applied": now}]
