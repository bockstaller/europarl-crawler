import os

import click
from dotenv import find_dotenv, load_dotenv


@click.group()
def cli():
    """Runs setup of the europarl-cli"""
    # .env-configuration file takes precedence over already loaded env-variables
    load_dotenv(override=True)


@click.command()
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    default=False,
    help="dry run operations and output their actions",
)
def init(dry_run):
    pass


cli.add_command(init)
