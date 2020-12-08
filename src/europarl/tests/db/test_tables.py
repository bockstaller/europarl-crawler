import pytest
from europarl.db.tables import SessionDay
from psycopg2 import sql


def test_table_exists(db_interface):
    sessionDay = SessionDay(db_interface)
    assert sessionDay.table_exists()


def test_table_not_exists(db_interface):
    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("drop table {table} cascade").format(
                table=sql.Identifier(SessionDay.table_name)
            )
        )

    sessionDay = SessionDay(db_interface)
    assert sessionDay.table_exists() is False
