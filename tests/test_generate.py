from pymongo_migrate.main import dt


def test_get_migrations(mongo_migrate):
    assert [migration.name for migration in mongo_migrate.get_migrations()] == [
        "20150612230153",
        "20181123000000_gt_500",
    ]


def test_upgrade(mongo_migrate, db_collection):
    now = dt().replace(microsecond=0)
    mongo_migrate.upgrade()

    assert [
        migration_data["name"]
        for migration_data in db_collection.find()
        if migration_data["applied"] >= now
    ] == ["20150612230153", "20181123000000_gt_500"]


def test_downgrade(mongo_migrate):
    mongo_migrate.downgrade(None)
