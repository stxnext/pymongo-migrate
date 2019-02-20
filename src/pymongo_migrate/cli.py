import click

from pymongo_migrate.main import MongoMigrate


@click.group()
def cli():
    pass


@cli.command()
def graph():
    MongoMigrate()
    click.echo("")


if __name__ == "__main__":
    cli()
