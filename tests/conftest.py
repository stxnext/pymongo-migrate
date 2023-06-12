import random
import shutil
from datetime import timezone
from pathlib import Path
from typing import Dict

import pymongo
import pytest
from bson import CodecOptions

from pymongo_migrate.mongo_migrate import MongoMigrate

TEST_DIR = Path(__file__).parent


@pytest.fixture
def mongo_url():
    return "mongodb://localhost:27017/"


@pytest.fixture
def db_name():
    random_id = random.randint(100, 10_000_000)  # nosec
    return f"test_{random_id}"


@pytest.fixture
def db_uri(mongo_url, db_name):
    return f"{mongo_url}{db_name}"


@pytest.fixture
def db(mongo_url, db_name):
    client = pymongo.MongoClient(mongo_url)
    yield client[db_name]
    client.drop_database(db_name)
    client.close()


@pytest.fixture
def db_collection(db):
    return db.get_collection(
        "pymongo_migrate",
        codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc),
    )


def _dir_contents(dir_path: Path) -> Dict[str, str]:
    dir_contents = {}
    for file_ in dir_path.iterdir():
        if file_.is_file():
            with file_.open() as f:
                dir_contents[f.name] = f.read()
    return dir_contents


@pytest.fixture(scope="session")
def migrations_dir(tmp_path_factory):
    original_migrations_path = TEST_DIR / "migrations"
    migrations_path = tmp_path_factory.mktemp("test_session") / "migrations"
    shutil.copytree(original_migrations_path, migrations_path)
    pre_contents = _dir_contents(migrations_path)
    yield str(migrations_path)
    assert pre_contents == _dir_contents(
        migrations_path
    ), "Migrations mangled during tests"


@pytest.fixture
def mongo_migrate(db_uri, db_name, db, migrations_dir):
    mm = MongoMigrate(
        pymongo.MongoClient(db_uri), db_name, migrations_dir=migrations_dir
    )
    yield mm
    mm.client.close()


@pytest.fixture()
def get_db_migrations(db_collection):
    def getter():
        return list(db_collection.find(projection={"_id": False}, sort=[("name", 1)]))

    return getter
