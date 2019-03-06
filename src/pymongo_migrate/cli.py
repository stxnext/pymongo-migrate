import os
from functools import wraps
from typing import Optional

import click

from pymongo_migrate.graph_draw import dump
from pymongo_migrate.mongo_migrate import MongoMigrate


@click.group()
def cli():
    pass


def mongo_migrate_decor(f):
    @wraps(f)
    def wrap_with_client(uri, migrations, collection, *args, **kwargs):
        mongo_migrate = MongoMigrate(
            mongo_uri=uri, migrations_dir=migrations, migrations_collection=collection
        )
        return f(mongo_migrate, *args, **kwargs)

    return wrap_with_client


def mongo_migration_options(f):
    decorators = [
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
        mongo_migrate_decor,
    ]
    for decorator in reversed(decorators):
        f = decorator(f)
    return f


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


@cli.command(
    short_help="automagically apply necessary upgrades or downgrades to reach target migration"
)
@mongo_migration_options
@click.argument("migration", required=False)
def migrate(mongo_migrate, migration=None):
    mongo_migrate.migrate(migration)


@cli.command(short_help="apply necessary upgrades to reach target migration")
@mongo_migration_options
@click.argument("migration", required=False)
def upgrade(mongo_migrate, migration=None):
    mongo_migrate.upgrade(migration)


@cli.command(short_help="apply necessary downgrades to reach target migration")
@mongo_migration_options
@click.argument("migration")
def downgrade(mongo_migrate, migration):
    mongo_migrate.downgrade(migration)


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
