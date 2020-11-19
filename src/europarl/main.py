import os
import random
import time

import click
from dotenv import find_dotenv, load_dotenv

indent = "    "


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
    setup_postgres()
    setup_redis()


cli.add_command(init)


def setup_postgres():
    click.secho("Postgres:", bold=True, underline=True)
    check_pg_connection()
    check_table_structure()
    create_table_structure()


def check_pg_connection():
    click.echo(indent + "Connection: ", nl=False)
    time.sleep(random.random())
    click.echo("✅")


def check_table_structure():
    click.echo(indent + "Table structure available: ", nl=False)
    time.sleep(random.random())
    click.echo("❌")


def create_table_structure():
    click.echo(indent + "Table structure created: ", nl=False)
    time.sleep(random.random())
    click.echo("✅")


def setup_redis():
    click.secho("Redis:", bold=True, underline=True)
    check_redis_connection()


def check_redis_connection():
    click.echo(indent + "Connection: ", nl=False)
    time.sleep(random.random())
    click.echo("✅")
