import pytest
from click.testing import CliRunner

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
