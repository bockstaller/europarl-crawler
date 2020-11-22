import os
import random
import time

import click
import psycopg2
from dotenv import load_dotenv
from europarl.db.interface import DBInterface
from europarl.db.tables import Table

indent = "    "


def main():
    load_dotenv(override=True)
    cli()


@click.group()
@click.option("--db_name", help="database name", envvar="EUROPARL_DB_NAME")
@click.option("--db_user", help="database user", envvar="EUROPARL_DB_USER")
@click.option("--db_password", help="database password", envvar="EUROPARL_DB_PASSWORD")
@click.option("--db_host", help="database host", envvar="EUROPARL_DB_HOST")
@click.option("--db_port", help="database port", envvar="EUROPARL_DB_PORT")
@click.pass_context
def cli(ctx, db_name, db_user, db_password, db_host, db_port):
    """Runs setup of the europarl-cli"""
    # ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # try to create a db connection
    ctx.obj["DB"] = DBInterface(
        name=db_name, user=db_user, password=db_password, host=db_host, port=db_port
    )


@click.command()
@click.pass_context
def init(ctx):
    db = ctx.obj["DB"]

    click.secho("Postgres:", bold=True, underline=True)

    click.echo(indent + "Checking if conncection is valid: ", nl=False)
    if db.check_connection():
        click.echo("✅")
    else:
        click.echo("❌")

    click.echo(indent + "Checking if table structure is available: ")

    for table in db.tables:
        click.secho(indent + str(table.__name__) + ":", bold=True)
        instance = table(ctx.obj["DB"])

        click.echo(indent + "Does the table exist: ", nl=False)
        if instance.table_exists() is True:
            click.echo("✅")
        else:
            click.echo("💬")
            click.echo(indent + "Creating table: ", nl=False)
            if instance.create_table():
                click.echo("✅")
            else:
                click.echo("❌")


cli.add_command(init)
