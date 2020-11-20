from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
from psycopg2 import sql

from .tables import Table


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


class DBInterface:
    """
    docstring
    """

    tables = get_all_subclasses(Table)

    def __init__(self, name, user, password, host, port):
        self.name = name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        pass

    def check_connection(self):
        try:
            con = self.db_connection()
            con.close()
            return True
        except Exception:
            return False
        finally:
            con.close()

    def db_connection(self):
        return psycopg2.connect(
            dbname=self.name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )

    @contextmanager
    def cursor(self, *args, **kwds):
        # Code to acquire resource, e.g.:
        connection = self.db_connection()
        cursor = connection.cursor()

        db = {"con": connection, "cur": cursor}
        db = SimpleNamespace(**db)

        try:
            yield db
        finally:
            # Code to release resource, e.g.:
            connection.commit()
            cursor.close()
            connection.close()
