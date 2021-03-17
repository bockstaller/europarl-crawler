from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql


def create_table_structure(config):
    from europarl.db import tables

    temp_db = DBInterface(config=config["General"])

    for table in tables:
        table_inst = table(temp_db)
        if not table_inst.table_exists():
            table_inst.create_table()
        del table_inst

    temp_db.close()


class DBInterface:
    """
    Manages the db-connection by storing connection details, tests the connection and providing a custom context manager.
    """

    connection_name = "europarl-crawler"
    connection = None

    def __init__(
        self,
        name=None,
        user=None,
        password=None,
        host=None,
        port=None,
        config=None,
    ):
        """Creates a DBInterface instance
        Stores the connection details in the instance and
        exists.
        Doesn't test the connection

        Args:
            name string: name of the db
            user string: name of the db user
            password string: passwort for the db user
            host string: hostname/adress to connect to
            port number: host port to connect to
        """
        if config:
            self.name = config["dbname"]
            self.user = config["dbuser"]
            self.password = config["dbpassword"]
            self.host = config["dbhost"]
            self.port = config["dbport"]
        else:
            self.name = name
            self.user = user
            self.password = password
            self.host = host
            self.port = port

    def connect(self):
        """Creates a db connection and stores it in the instance
        Reopens already closed connections.

        Returns:
            psycopg2.connection: returns a psycopg2-connection-instance
        """
        if self.connection:
            if self.connection.closed == 0:
                # return early if we have an open connection
                return self.connection

        self.connection = psycopg2.connect(
            dbname=self.name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            application_name=self.connection_name,
        )
        return self.connection

    def close(self):
        """
        Closes the database connection
        """
        if self.connection:
            if self.connection.closed == 0:
                self.connection.close()
                self.connection = None

    def __del__(self):
        """
        Cleans up after itself and closes the database connection by calling close()
        """
        self.close()

    @contextmanager
    def cursor(self, *args, **kwargs):
        """Context manager which returns a namespace consisting out of a
        psycopg2 connection and cursor object.
        Both can be accessed via dot-notation

        This contextmanager automatically commits the changes after exiting
        the context.

        Yields:
            "cursor"-namespace : Namespace with the elements "con" and "cur"
        """
        # Code to acquire the db connection
        self.connect()
        cursor = self.connection.cursor(*args, **kwargs)

        db = {"con": self.connection, "cur": cursor}
        db = SimpleNamespace(**db)

        try:
            yield db
        finally:

            self.connection.commit()
            cursor.close()
