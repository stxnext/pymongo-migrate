import random
from pathlib import Path

import pymongo
import pytest

from pymongo_migrate.main import MongoMigrate

TEST_DIR = Path(__file__).parent


@pytest.fixture()
def mongo_url():
    return "mongodb://localhost:27017/"


@pytest.fixture(scope="module")
def db_name():
    return f"test_{random.randint(100, 10000000)}"


def db(mongo_url, db_name):
    client = pymongo.MongoClient(mongo_url)
    yield
    client.drop_database(db_name)


@pytest.fixture
def mongo_migrate(mongo_url, db_name):
    return MongoMigrate(
        mongo_uri=f"{mongo_url}{db_name}", migrations_dir=str(TEST_DIR / "migrations")
    )
