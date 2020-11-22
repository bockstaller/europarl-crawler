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
    """

    schema = "public"
    table_name = "session_days"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            date date NOT NULL,
                            hit boolean NOT NULL,
                            checked boolean NOT NULL,
                            checked_at time without time zone,
                            PRIMARY KEY(date)
                          );"""
