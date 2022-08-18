import logging
import os
import sys
from functools import wraps
from pprint import pformat
from typing import Optional

import click
import pymongo.monitoring

from pymongo_migrate.graph_draw import dump
from pymongo_migrate.mongo_migrate import MongoMigrate


@click.group()
def cli():
    pass


class CommandLogger(pymongo.monitoring.CommandListener):
    def __init__(self, verbose: int = 0):
        self.verbose = verbose

    def echo(self, *args, min_verbosity=1):
        if self.verbose >= min_verbosity:
            click.echo(*args)

    def started(self, event):
        self.echo(f"Command {event.command_name}#{event.request_id} STARTED")
        if self.verbose >= 1:
            self.echo(pformat(event.command), min_verbosity=1)

    def succeeded(self, event):
        self.echo(
            f"Command {event.command_name}#{event.request_id} SUCCEEDED in {event.duration_micros}us"
        )

    def failed(self, event):
        self.echo(
            f"Command {event.command_name}#{event.request_id} FAILED in {event.duration_micros}us"
        )


def get_logger(verbose: int):
    logger = logging.getLogger(__name__)

    stream = click.get_text_stream("stdout")
    console_handler = logging.StreamHandler(stream=stream)
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    if verbose > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def mongo_migrate_decor(f):
    @wraps(f)
    def wrap_with_client(uri, migrations, collection, verbose, *args, **kwargs):
        mongo_migrate = MongoMigrate(
            client=pymongo.MongoClient(
                uri, event_listeners=[CommandLogger(verbose=verbose)]
            ),
            migrations_dir=migrations,
            migrations_collection=collection,
            logger=get_logger(verbose),
        )
        return f(mongo_migrate, *args, **kwargs)

    return wrap_with_client


def add_project_root_to_python_path_decorator(f):
    @wraps(f)
    def inner(project_root, *args, **kwargs):
        if project_root is not None:
            sys.path.append(project_root)
        return f(*args, **kwargs)

    return inner


def _decorate(f, *decorators):
    for decorator in reversed(decorators):
        f = decorator(f)
    return f


def mongo_migration_options(f):
    return _decorate(
        f,
        click.option(
            "-u",
            "--uri",
            default=None,
            envvar="PYMONGO_MIGRATE_URI",
            help="mongodb URI",
        ),
        click.option(
            "-m",
            "--migrations",
            default=MongoMigrate.migrations_dir,
            envvar="PYMONGO_MIGRATE_MIGRATIONS",
            help="migration script directory",
            show_default=True,
        ),
        click.option(
            "-c",
            "--collection",
            default=MongoMigrate.migrations_collection,
            envvar="PYMONGO_MIGRATE_COLLECTION",
            help="mongodb collection used for storing migration states",
            show_default=True,
        ),
        click.option("-v", "--verbose", count=True),
        click.option(
            "-p",
            "--project_root",
            default=None,
            envvar="PYMONGO_MIGRATE_PROJECT_ROOT",
            help="project_root will be added to python path",
            show_default=True,
        ),
        add_project_root_to_python_path_decorator,
        mongo_migrate_decor,
    )


@cli.command(short_help="show migrations and their status")
@mongo_migration_options
def show(mongo_migrate):
    name_len_max = max(
        (len(migration.name) for migration in mongo_migrate.get_migrations()), default=0
    )

    migration_column_name = "Migration name".ljust(name_len_max)
    click.secho(f"{migration_column_name}\tApplied timestamp", fg="yellow")
    for migration in mongo_migrate.get_migrations():
        migration_state = mongo_migrate.get_state(migration)
        if migration_state.applied:
            applied_text = click.style(migration_state.applied.isoformat(), fg="green")
        else:
            applied_text = click.style("Not applied", fg="red")
        click.echo(f"{migration.name.ljust(name_len_max)}\t" + applied_text)


def migrate_cmd_options(f):
    return _decorate(
        f,
        mongo_migration_options,
        click.argument("migration", required=False),
        click.option("--fake", is_flag=True),
    )


@cli.command(
    short_help="automagically apply necessary upgrades or downgrades to reach target migration"
)
@migrate_cmd_options
def migrate(mongo_migrate, migration=None, fake=False):
    mongo_migrate.migrate(migration, fake=fake)


@cli.command(short_help="apply necessary upgrades to reach target migration")
@migrate_cmd_options
def upgrade(mongo_migrate, migration=None, fake=False):
    mongo_migrate.upgrade(migration, fake=fake)


@cli.command(short_help="apply necessary downgrades to reach target migration")
@migrate_cmd_options
def downgrade(mongo_migrate, migration, fake=False):
    mongo_migrate.downgrade(migration, fake=fake)


@cli.command()
@mongo_migration_options
@click.argument("name", required=False)
def generate(mongo_migrate, name: Optional[str] = None):
    click.echo(f"Generating new migration in {mongo_migrate.migrations_dir}")
    file_path = mongo_migrate.generate(name)
    click.echo(
        "Generated: "
        + click.style(f"{file_path.parent}{os.sep}", fg="bright_black")
        + click.style(file_path.stem, fg="green")
        + click.style(file_path.suffix, fg="bright_black")
    )


@cli.command()
@mongo_migration_options
def graph(mongo_migrate):
    stdout = click.get_text_stream("stdout")
    dump(mongo_migrate.graph, stdout)


if __name__ == "__main__":
    cli()
