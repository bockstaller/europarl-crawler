import os

import click


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--dry-run", "-d", is_flag=True, default=False, help="dry run all operations"
)
def init(dry_run):
    if dry_run:
        print("dry_run")
    print("Initialize database")
    print("Migrate database")


cli.add_command(init)
