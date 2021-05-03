#!/usr/bin/python3.9

import datetime
import json
import logging
import os
import traceback

import click
import click_log
import requests
from beautifultable import BeautifulTable
from elasticsearch import Elasticsearch, helpers

import europarl.jobs.crawler as ep_crawler
import europarl.jobs.indexer as ep_indexer
import europarl.jobs.postprocessor as ep_postprocessor
from europarl import configuration, rules
from europarl.db import DBInterface, Documents, Rules, create_table_structure
from europarl.downloader import download_all_docs, get_unviewed_date, spaced_out_dates
from europarl.elasticinterface import create_index, get_current_index, index_documents

logger = logging.getLogger("eurocli")
click_log.basic_config("eurocli")


def main():
    """
    CLI wrapper.
    Creates only the context object
    """
    return cli(obj={})


@click.group()
@click.pass_context
def cli(ctx):
    """
    CLI entrypoint.
    """
    pass


def load_config(ctx):
    "Loads the configuration and establishes db and elasticsearch connections"
    config = configuration.read()
    ctx.obj["config"] = config

    ctx.obj["db"] = DBInterface(config=config["General"])

    ctx.obj["index"] = config["Indexer"].get("ESIndexname")
    ctx.obj["es"] = Elasticsearch(config["Indexer"].get("ESConnection"))
    pass


@click.group()
@click.pass_context
def crawler(ctx):
    load_config(ctx)
    pass


cli.add_command(crawler)


@click.command(name="start")
def crawler_start():
    """
    Function for ``eurocli crawler start``.
    Calls the main of the crawler job.
    """
    click.echo("Starting crawler")
    ep_crawler.main()


crawler.add_command(crawler_start)


@click.command("rules")
@click.option("--rule", "-r", help="Rule to change", multiple=True)
@click.option("--activate/--deactivate", default=False)
@click.pass_context
def rules_function(ctx, rule, activate):
    """
    Function for ``eurocli rules [...]``

    Args:
        ctx (context): context object
        rule (int): id('s) of the rule to modify
        activate (boolean): target state of the rule
    """
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
    load_config(ctx)
    pass


cli.add_command(postprocessing)


@click.command("start")
def postprocessing_start():
    """
    Function for ``eurocli postprocessing start``.
    Calls the main of the postprocessing job.
    """
    click.echo("Starting postprocessing")
    ep_postprocessor.main()


@click.command("reset")
@click.option(
    "--rule", "-r", help="Select documents to reset by their rules", multiple=True
)
@click.option("-f", "--force", is_flag=True)
@click.pass_context
def postprocessing_reset(ctx, rule, force):
    """
    Function for ``eurocli postprocessing reset [...]``

    Args:
        ctx (context): context object
        rule (int): id('s) of the rule which documents should be reset
        force (boolean): unindexing failures are ignored if true
    """
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
    load_config(ctx)
    pass


cli.add_command(indexing)


@click.command(name="start")
def indexing_start():
    """
    Function for ``eurocli indexing start``.
    Calls the main of the indexing job.
    """
    click.echo("Starting indexing")
    ep_indexer.main()


@click.command(name="unindex")
@click.pass_context
def indexing_unindex(ctx):
    """
    Function for ``eurocli indexing unindex``
    Unindexes all documents which are marked for unindexing
    """
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
    """
    Function for ``eurocli indexing reindex [...]``
    Creates a new mapping from the passed .json file and starts a reindexing background job

    Args:
        ctx (context): context object
        mapping (str): path to a mapping.json
    """

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


@click.group()
def download():
    pass


cli.add_command(download)


@click.command("sessions")
@click_log.simple_verbosity_option(logger)
@click.option(
    "--rule",
    "-r",
    help="Select session documents to download. Use rulenames",
)
@click.option(
    "--backfill/--no-backfill",
    default=False,
    help="Backfill older documents by using a not yet seen date.",
)
@click.option(
    "--refresh/--no-refresh",
    default=False,
    help="Refresh older documents using an exponential backoff.",
)
@click.argument(
    "directory",
)
@click.option("--retry", default=3, help="Number of retries per document")
@click.option("--sleep", default=3, help="Wait time between document downloads")
@click.option("-d", "--date", help="Date to download documents for")
def download_sessions(rule, backfill, refresh, date, retry, sleep, directory):
    if not date:
        date = datetime.date.today()
        logger.info("No date provided. Using {}".format(date.strftime("%Y-%m-%d")))

    if backfill:
        date = get_unviewed_date(directory=directory, date=date)
        if date is None:
            logger.info("No date for backfilling found. Aborting")
            return
        else:
            logger.info(
                "Using {} as backfilling date".format(date.strftime("%Y-%m-%d"))
            )

    if refresh:
        dates = spaced_out_dates(date)
    else:
        dates = [date]

    logger.info(
        "Crawling the following dates {}".format(
            [date.strftime("%Y-%m-%d") for date in dates]
        )
    )

    rulelist = [r.strip() for r in rule.split()]

    logger.info("Using the following rules: {}".format(rulelist))

    for date in dates:
        try:
            download_all_docs(
                basedir=directory,
                rulenames=rulelist,
                date=date,
                retry=retry,
                sleep=sleep,
            )

            if backfill:
                ledger = os.path.join(directory, "backfilled_dates.txt")
                with open(ledger, mode="r+") as f:
                    backfilled_dates = [line.strip() for line in f if line]
                    if date.strftime("%Y-%m-%d") not in backfilled_dates:
                        f.write(date.strftime("%Y-%m-%d") + "\n")
                        logger.debug(
                            "Adding new date {} to backfilled dates protocol".format(
                                date.strftime("%Y-%m-%d")
                            )
                        )

        except Exception as e:
            logger.error(e, exc_info=True)


download.add_command(download_sessions)


@click.command("texts")
@click.option(
    "--rule",
    "-r",
    help="Select text rules to download.  Use rulenames",
    multiple=True,
)
@click.option("--dir")
@click.option("--min", default=1)
@click.option("--max", default=500)
@click.pass_context
def download_texts(ctx, dir, rule, min, max):
    return


download.add_command(download_texts)


if __name__ == "__main__":
    cli(obj={})
