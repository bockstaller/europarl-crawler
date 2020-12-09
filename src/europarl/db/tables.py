import datetime
from abc import ABC
from contextlib import contextmanager
from datetime import timezone
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql


class Table(ABC):
    """
    Abstract baseclass implementing common table functions


    """

    def __init__(self, DBInterface):
        """Creates a new instance of the table class

        Args:
            DBInterface (DBInterface): DBInterface instance to execute the commands
        """
        self.db = DBInterface

    def __del__(self):
        """
        Forces destructor call of DBInterface and therefore
        closes database connection
        """
        self.db.close()

    def create_table(self):
        """Creates the table in the database by executing it's table definition

        Returns:
            boolean: True if the table was created successfully
        """

        with self.db.cursor() as db:
            db.cur.execute(
                sql.SQL(self.table_definition).format(
                    schema=sql.Identifier(self.schema),
                    table=sql.Identifier(self.table_name),
                )
            )

    def table_exists(self):
        """Checks if the table exists in the database

        Returns:
            boolean: True if the table exists in the database
        """

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
