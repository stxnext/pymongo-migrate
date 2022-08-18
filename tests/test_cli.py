import sys
from pathlib import Path

import freezegun
import pytest
from click.testing import CliRunner
from utils import generate_str

from pymongo_migrate.cli import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture()
def invoker(cli_runner):
    def invoke_wrap(*args, **kwargs):
        return cli_runner.invoke(cli, *args, **kwargs)

    return invoke_wrap


def test_show(invoker, db, db_uri, migrations_dir):
    result = invoker(
        ["show", "-u", db_uri, "-m", migrations_dir], catch_exceptions=False
    )

    assert (
        result.stdout
        == """\
Migration name       	Applied timestamp
20150612230153       	Not applied
20181123000000_gt_500	Not applied
"""
    )


@freezegun.freeze_time("2019-02-03 04:05:06")
def test_generate(invoker, db, db_uri, tmp_path):
    migrations_path = tmp_path / "migrations"
    result = invoker(
        ["generate", "-u", db_uri, "-m", str(migrations_path)], catch_exceptions=False
    )
    filename = "20190203040506.py"
    assert filename in result.stdout
    files = {f.name: f for f in migrations_path.iterdir()}
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


def test_migrate(invoker, db, db_uri, migrations_dir):
    result = invoker(
        ["migrate", "-u", db_uri, "-m", migrations_dir], catch_exceptions=False
    )

    assert "Running upgrade migration '20150612230153'" in result.stdout


def test_migrate_fake(invoker, db, db_uri, migrations_dir):
    result = invoker(
        ["migrate", "-u", db_uri, "-m", migrations_dir, "--fake"],
        catch_exceptions=False,
    )

    assert "Fake running upgrade migration '20150612230153'" in result.stdout


def test_migrate_verbose(invoker, db, db_uri, migrations_dir):
    result = invoker(
        ["migrate", "-u", db_uri, "-m", migrations_dir, "-vv"], catch_exceptions=False
    )

    assert "Command update#" in result.stdout


def test_that_arg_project_root_is_added_to_python_path(
    invoker,
    db,
    db_uri,
    migrations_dir,
):
    rnd_path = Path(generate_str())
    assert str(rnd_path) not in sys.path
    invoker(
        ["show", "-u", db_uri, "-m", migrations_dir, "-p", rnd_path],
        catch_exceptions=False,
    )
    assert str(rnd_path) in sys.path
