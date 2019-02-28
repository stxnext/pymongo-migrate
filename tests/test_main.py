import freezegun

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


@freezegun.freeze_time("2019-02-25 01:13:56")
def test_generate(mongo_migrate, tmp_path):
    tmp_migrations_path = tmp_path / "migrations"
    tmp_migrations_path.mkdir()
    mongo_migrate.migrations_dir = str(tmp_migrations_path)
    mongo_migrate.generate()
    files = {f.name: f for f in tmp_migrations_path.iterdir()}
    assert set(files) == {"201902011356.py"}
    with files["201902011356.py"].open() as f:
        content = f.read()
        assert (
            content
            == '''\
"""
Migration description here!
"""
name = '201902011356'
dependencies = ['20181123000000_gt_500']


def upgrade(db: "pymongo.database.Database"):
    pass


def downgrade(db: "pymongo.database.Database"):
    pass
'''
        )
