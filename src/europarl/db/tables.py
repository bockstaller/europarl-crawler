from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql


class Table:
    def __init__(self, DBInterface):
        self.db = DBInterface

    def create_table(self):
        try:
            with self.db.cursor() as db:
                db.cur.execute(
                    sql.SQL(self.table_definition).format(
                        schema=sql.Identifier(self.schema),
                        table=sql.Identifier(self.table_name),
                    )
                )
                return True
        except Exception:
            return False

    def table_exists(self):
        with self.db.cursor() as db:

            db.cur.execute(
                sql.SQL(
                    """ SELECT EXISTS
                        (
                            SELECT 1
                            FROM pg_tables
                            WHERE schemaname = {schema}
                            AND tablename = {table}
                        )
                    """
                ).format(
                    schema=sql.Literal(self.schema),
                    table=sql.Literal(self.table_name),
                )
            )
            return db.cur.fetchone()[0]


class SessionDay(Table):
    """
    Models the days the parliament met

    Contains:
        date: the date of a possible session
        hit: did HEAD-ing a generated result not return a 404
        urls_created: True if a url generator has already derived urls from the date
        urls_created_ts: When did a url generator derive urls from the date

    """

    schema = "public"
    table_name = "session_days"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id integer NOT NULL,
                            date date NOT NULL,
                            hit boolean NOT NULL,
                            urls_created boolean NOT NULL,
                            urls_created_ts datetime,
                            PRIMARY KEY(id)
                          );"""


class URLs(Table):
    """
    Stores information about URLs

    Contains:
        rule: name of the rule used to generate the URL
        url: the generated URL
        found: True if a crawler found this URL in a document
        enqueued: True if the URLGenerator has enqueued the URL to be crawled, is set to False on startup
        crawled: has this URL been crawled
        crawled_at: when has this URL been crawled
        file_path: where is the downloaded document stored
        recrawl: should this file been recrawled
        recrawl_after: the document will be recrawled sometime after this timestamp

    """

    schema = "public"
    table_name = "urls"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id integer NOT NULL,
                            rule VARCHAR() NOT NULL,
                            url TEXT NOT NULL
                            found boolean NOT NULL,
                            created datetime NOT NULL,
                            enqueued boolean NOT NULL,
                            enqueued_at datetime,
                            enqueued_times integer NOT NULL,
                            crawled boolean NOT NULL,
                            crawled_at datetime,
                            failed boolean NOT NULL,
                            file_path TEXT,
                            recrawl boolean NOT NULL,
                            recrawl_after datetime,
                            PRIMARY KEY(id)
                          );"""
