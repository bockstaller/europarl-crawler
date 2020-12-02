from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql

from .tables import Table


def get_all_subclasses(cls):
    """Get all subclasses and sub-sub-...-classes of a class

    Returns:
        list: List containing all sub-classes
    """
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


class DBInterface:
    """
    Manages the db-connection.
    - stores connection details
    - tests the connection
    - implements a custom context manager
    """

    # TODO: Don't create connections in the cursor context manager. This creates shortlifed postgres connections

    tables = get_all_subclasses(Table)

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

    def check_connection(self):
        """Tests if a connection to the db is possible

        Returns:
            boolean: returns True if a connection to the db can be established
        """
        try:
            con = self.connect()
            con.close()
            return True
        except Exception:
            return False
        finally:
            con.close()

    def connect(self):
        """Creates a db connection

        Returns:
            psycopg2.connection: returns a psycopg2-connection-instance
        """
        return psycopg2.connect(
            dbname=self.name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )

    @contextmanager
    def cursor(self, *args, **kwargs):
        """Context manager which returns a namespace consisting out of a
        psycopg2 connection and cursor object.
        Both can be accessed via dot-notation

        Yields:
            "cursor"-namespace : Namespace with the elements "con" and "cur"
        """
        # Code to acquire the db connection
        connection = self.connect()
        cursor = connection.cursor()

        db = {"con": connection, "cur": cursor}
        db = SimpleNamespace(**db)

        try:
            yield db
        finally:
            # Code to release the db connection
            connection.commit()
            cursor.close()
            connection.close()
