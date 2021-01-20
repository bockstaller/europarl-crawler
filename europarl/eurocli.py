import click
from beautifultable import BeautifulTable

import europarl.crawler as ep_crawler
import europarl.postprocessor as ep_postprocessor
from europarl.crawler import create_table_structure, init_rules, read_config
from europarl.db import DBInterface, Documents, Rules


@click.group()
@click.pass_context
def main(ctx):
    config = ep_crawler.read_config()
    db = DBInterface(config=config["General"])
    ctx.obj["config"] = config
    ctx.obj["db"] = db
    pass


@click.group()
def crawler():
    pass


main.add_command(crawler)


@click.command()
def crawler_start(name="start"):
    click.echo("Starting crawler")
    ep_crawler.main()


crawler.add_command(crawler_start)


@click.command()
@click.option("--rule", "-r", help="Rule to change", multiple=True)
@click.option("--activate/--deactivate", default=False)
@click.pass_context
def rules(ctx, rule, activate):
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


main.add_command(rules)


@click.group()
@click.pass_context
def postprocessing(ctx):
    pass


main.add_command(postprocessing)


@click.command("start")
def postprocessing_start():
    click.echo("Starting postprocessing")
    ep_postprocessor.main()


@click.command("reset")
@click.option(
    "--rule", "-r", help="Select documents to reset by their rules", multiple=True
)
@click.pass_context
def postprocessing_reset(ctx, rule):
    click.echo("Resetting postprocessing results")
    d = Documents(ctx.obj["db"])
    if rule:
        for ru in rule:
            try:
                d.reset_postprocessing_by_rule(ru)
            except Exception as e:
                print(e)
    else:
        d.reset_all_postprocessing()


postprocessing.add_command(postprocessing_reset)
postprocessing.add_command(postprocessing_start)

if __name__ == "__main__":
    main(obj={})
