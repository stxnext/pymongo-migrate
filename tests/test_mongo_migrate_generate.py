import freezegun
import pymongo
import pytest
from pymongo_migrate.mongo_migrate import MongoMigrate


@freezegun.freeze_time("2019-02-25 01:13:56")
def test_generate(mongo_migrate, tmp_path):
    tmp_migrations_path = tmp_path / "test_generate_migrations"
    mongo_migrate.migrations_dir = str(tmp_migrations_path)
    filename = mongo_migrate.generate().name
    assert filename == "20190225011356.py"
    files = {f.name: f for f in tmp_migrations_path.iterdir()}
    assert set(files) == {filename}
    with files[filename].open() as f:
        content = f.read()
        assert (
            content
            == '''\
"""
Migration description here!
"""
name = '20190225011356'
dependencies = ['20181123000000_gt_500']


def upgrade(db: "pymongo.database.Database"):
    pass


def downgrade(db: "pymongo.database.Database"):
    pass
'''
        )


@pytest.fixture
def empty_migrations_dir(tmp_path):
    yield tmp_path / "migrations"


@pytest.fixture
def mongo_migrate_with_empty_dir(db_uri, db_name, db, empty_migrations_dir):
    mm = MongoMigrate(
        pymongo.MongoClient(db_uri), db_name, migrations_dir=str(empty_migrations_dir)
    )
    yield mm
    mm.client.close()


@freezegun.freeze_time("2019-02-03 04:05:06")
def test_generate_initial_migration(mongo_migrate_with_empty_dir, empty_migrations_dir):
    mongo_migrate = mongo_migrate_with_empty_dir
    filename = mongo_migrate.generate().name
    assert filename == "20190203040506.py"
    files = {f.name: f for f in empty_migrations_dir.iterdir()}
    assert set(files) == {filename}
    with files[filename].open() as f:
        content = f.read()
        assert (
            content
            == '''\
"""
Migration description here!
"""
name = '20190203040506'
dependencies = []


def upgrade(db: "pymongo.database.Database"):
    pass


def downgrade(db: "pymongo.database.Database"):
    pass
'''
        )


def test_generate_should_fail_when_name_collides(mongo_migrate):
    with pytest.raises(FileExistsError):
        mongo_migrate.generate("20181123000000_gt_500")
