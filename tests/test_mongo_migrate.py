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


def test_downgrade(mongo_migrate, db, get_db_migrations):
    mongo_migrate.downgrade(None)
    db_migrations = get_db_migrations()
    assert db_migrations == []
    assert db.list_collection_names() == []


def test_upgrade_n_downgrade(mongo_migrate, db, get_db_migrations):
    mongo_migrate.upgrade()
    mongo_migrate.downgrade(None)
    db_migrations = get_db_migrations()
    assert db_migrations == [
        {"applied": None, "name": "20150612230153"},
        {"applied": None, "name": "20181123000000_gt_500"},
    ]
    assert db.list_collection_names() == ["pymongo_migrate"]
