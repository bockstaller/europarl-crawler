#!/usr/bin/python3.9

import json

import click
from beautifultable import BeautifulTable
from elasticsearch import Elasticsearch, helpers

import europarl.jobs.crawler as ep_crawler
import europarl.jobs.indexer as ep_indexer
import europarl.jobs.postprocessor as ep_postprocessor
from europarl import configuration, rules
from europarl.db import DBInterface, Documents, Rules, create_table_structure
from europarl.elasticinterface import create_index, get_current_index, index_documents


def main():
    return cli(obj={})


@click.group()
@click.pass_context
def cli(ctx):
    config = configuration.read()
    ctx.obj["config"] = config

    ctx.obj["db"] = DBInterface(config=config["General"])

    ctx.obj["index"] = config["General"].get("ESIndexname")
    ctx.obj["es"] = Elasticsearch(config["General"].get("ESConnection"))
    pass


@click.group()
def crawler():
    pass


cli.add_command(crawler)


@click.command(name="start")
def crawler_start():
    click.echo("Starting crawler")
    ep_crawler.main()


crawler.add_command(crawler_start)


@click.command()
@click.option("--rule", "-r", help="Rule to change", multiple=True)
@click.option("--activate/--deactivate", default=False)
@click.pass_context
def rules_function(ctx, rule, activate):
    r = Rules(ctx.obj["db"])

    if rule:
        for ru in rule:
            try:
                r.update_rule_state(ru, activate)
            except Exception as e:
                print(e)

    values, keys = r.get_rules()
    table = BeautifulTable()
    table.columns.header = keys
    for row in values:
        table.rows.append(row)
    click.echo("Europarl Crawler rules:")
    click.echo(table)


cli.add_command(rules_function)


@click.group()
@click.pass_context
def postprocessing(ctx):
    pass


cli.add_command(postprocessing)


@click.command("start")
def postprocessing_start():
    click.echo("Starting postprocessing")
    ep_postprocessor.main()


@click.command("reset")
@click.option(
    "--rule", "-r", help="Select documents to reset by their rules", multiple=True
)
@click.option("-f", "--force", is_flag=True)
@click.pass_context
def postprocessing_reset(ctx, rule, force):
    click.echo("Resetting postprocessing results")

    d = Documents(ctx.obj["db"])
    if rule:
        for ru in rule:
            try:
                d.reset_postprocessing_by_rule(ru)
            except Exception as e:
                print(e)
    else:
        if force:
            click.echo("Resetting all postprocessing results")
            d.reset_all_postprocessing()
        else:
            click.echo("Force (-f) to reset all postprocessing results")

    documents = d.get_documents_to_unidex()

    current_index = get_current_index(ctx.obj["es"], ctx.obj["index"])

    successfull_ids = index_documents(
        ctx.obj["es"], d, "delete", current_index, documents, silent=True
    )
    click.echo(
        "Unindexed successfully {} documents out of {}".format(
            len(successfull_ids), len(documents)
        )
    )
    if force:
        click.echo("Force resetting all unindex flags")
        d.reset_unindex(documents)
    else:
        d.reset_unindex(successfull_ids)


postprocessing.add_command(postprocessing_reset)
postprocessing.add_command(postprocessing_start)


@click.group()
@click.pass_context
def indexing(ctx):
    pass


cli.add_command(indexing)


@click.command(name="start")
def indexing_start():
    click.echo("Starting indexing")
    ep_indexer.main()


@click.command(name="unindex")
@click.pass_context
def indexing_unindex(ctx):
    d = Documents(ctx.obj["db"])

    click.echo("Unindexing stale documents")
    documents = d.get_documents_to_unidex()

    current_index = get_current_index(ctx.obj["es"], ctx.obj["index"])

    successfull_ids = index_documents(
        ctx.obj["es"], d, "delete", current_index, documents, silent=True
    )

    click.echo(
        "Unindexed successfully {} documents out of {}".format(
            len(successfull_ids), len(documents)
        )
    )
    d.reset_unindex(successfull_ids)


@click.command(name="reindex")
@click.argument("mapping")
@click.pass_context
def indexing_reindex(ctx, mapping):
    click.echo("Reindexing")
    with open(mapping, "r") as file:
        mapping = json.load(file)

    current_index = get_current_index(ctx.obj["es"], ctx.obj["index"])
    new_index = create_index(ctx.obj["es"], ctx.obj["index"], mapping=mapping)

    source = {}
    source["index"] = current_index
    dest = {}
    dest["index"] = new_index
    body = {"source": source, "dest": dest}

    print(body)

    res = ctx.obj["es"].reindex(body, refresh=True, wait_for_completion=False)
    print(res)

    click.echo(new_index)


indexing.add_command(indexing_start)
indexing.add_command(indexing_unindex)
indexing.add_command(indexing_reindex)

if __name__ == "__main__":
    cli(obj={})
