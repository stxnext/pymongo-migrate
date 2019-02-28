import random
from datetime import timezone
from pathlib import Path

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


@pytest.fixture()
def migrations_dir():
    return str(TEST_DIR / "migrations")


@pytest.fixture
def mongo_migrate(db_uri, db_name, db, migrations_dir):
    mm = MongoMigrate(mongo_uri=db_uri, migrations_dir=migrations_dir)
    yield mm
    mm.client.close()
