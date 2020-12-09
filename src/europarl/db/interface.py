from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql


class DBInterface:
    """
    Manages the db-connection.
    - stores connection details
    - tests the connection
    - implements a custom context manager
    """

    def __init__(self, name, user, password, host="localhost", port=5432):
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
        self.name = name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

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
        cursor = self.connection.cursor()

        db = {"con": self.connection, "cur": cursor}
        db = SimpleNamespace(**db)

        try:
            yield db
        finally:

            self.connection.commit()
            cursor.close()
