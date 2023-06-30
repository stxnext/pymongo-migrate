from collections import defaultdict
from unittest.mock import Mock, patch

import freezegun
from pymongo_migrate.mongo_migrate import dt


def test_get_migrations(mongo_migrate):
    assert [migration.name for migration in mongo_migrate.get_migrations()] == [
        "20150612230153",
        "20181123000000_gt_500",
    ]


@freezegun.freeze_time("2019-02-03 04:05:06")
def test_upgrade(mongo_migrate, db, get_db_migrations):
    mongo_migrate.upgrade()

    db_migrations = get_db_migrations()
    assert db_migrations == [
        {"applied": dt(2019, 2, 3, 4, 5, 6), "name": "20150612230153"},
        {"applied": dt(2019, 2, 3, 4, 5, 6), "name": "20181123000000_gt_500"},
    ]

    assert db.numbers_collection.count_documents({}) == 499


@freezegun.freeze_time("2019-02-03 04:05:06")
def test_upgrade_fake(mongo_migrate, db, get_db_migrations):
    mongo_migrate.upgrade(fake=True)

    db_migrations = get_db_migrations()
    assert db_migrations == [
        {"applied": dt(2019, 2, 3, 4, 5, 6), "name": "20150612230153"},
        {"applied": dt(2019, 2, 3, 4, 5, 6), "name": "20181123000000_gt_500"},
    ]

    assert db.numbers_collection.count_documents({}) == 0


@freezegun.freeze_time("2019-02-03 04:05:06")
def test_upgrade_skip_applied(mongo_migrate, db, db_collection, get_db_migrations):
    db_collection.insert_one(
        {"applied": dt(2017, 10, 10, 10, 10, 10), "name": "20150612230153"}
    )

    migrations = {m.name: m for m in mongo_migrate.get_migrations()}
    upgrade_mocks = defaultdict(Mock)

    def patch_upgrade(name):
        return patch.object(migrations[name], "upgrade", upgrade_mocks[name])

    with patch_upgrade("20150612230153"), patch_upgrade("20181123000000_gt_500"):
        mongo_migrate.upgrade()
    upgrade_mocks["20150612230153"].assert_not_called()
    upgrade_mocks["20181123000000_gt_500"].assert_called()

    assert get_db_migrations() == [
        {"applied": dt(2017, 10, 10, 10, 10, 10), "name": "20150612230153"},
        {"applied": dt(2019, 2, 3, 4, 5, 6), "name": "20181123000000_gt_500"},
    ]


def test_downgrade(mongo_migrate, db, get_db_migrations):
    mongo_migrate.downgrade(None)
    db_migrations = get_db_migrations()
    assert db_migrations == []
    assert db.list_collection_names() == []


def test_downgrade_fake(mongo_migrate, db, get_db_migrations):
    mongo_migrate.upgrade()
    mongo_migrate.downgrade(fake=True)

    db_migrations = get_db_migrations()
    assert db_migrations == [
        {"applied": None, "name": "20150612230153"},
        {"applied": None, "name": "20181123000000_gt_500"},
    ]

    assert db.numbers_collection.count_documents({}) == 499


def test_upgrade_n_downgrade(mongo_migrate, db, get_db_migrations):
    mongo_migrate.upgrade()
    mongo_migrate.downgrade(None)
    db_migrations = get_db_migrations()
    assert db_migrations == [
        {"applied": None, "name": "20150612230153"},
        {"applied": None, "name": "20181123000000_gt_500"},
    ]
    assert db.list_collection_names() == ["pymongo_migrate"]


def test_migrate(mongo_migrate):
    """migrate without args should work as upgrade"""
    with patch.object(mongo_migrate, "upgrade") as upgrade_mock:
        mongo_migrate.migrate()
    upgrade_mock.assert_called()
