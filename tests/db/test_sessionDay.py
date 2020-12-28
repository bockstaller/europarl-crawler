import datetime

import pytest
from psycopg2 import sql

from europarl.db import SessionDay


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


@pytest.mark.parametrize(
    "start_date,offset,limit,expected_len",
    [
        (
            datetime.date.today() - datetime.timedelta(days=9),
            datetime.timedelta(days=0),
            100,
            10,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=9),
            datetime.timedelta(days=0),
            5,
            5,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=9),
            datetime.timedelta(days=5),
            100,
            5,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=0),
            datetime.timedelta(days=0),
            100,
            1,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=0),
            datetime.timedelta(days=5),
            100,
            0,
        ),
    ],
)
def test_SessionDays_get_unchecked_days(
    db_interface, start_date, offset, limit, expected_len
):
    sessionDay = SessionDay(db_interface)
    dates = sessionDay.get_unchecked_days(
        limit=limit, start_date=start_date, offset=offset
    )
    assert len(dates) == expected_len

    d1 = start_date
    d2 = datetime.date.today() - offset
    days = [d1 + datetime.timedelta(days=x) for x in range((d2 - d1).days + 1)]

    assert all(elem in days for elem in dates)


@pytest.mark.parametrize(
    "date, hit",
    [
        (
            datetime.date.today() - datetime.timedelta(days=0),
            False,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=1),
            False,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=2),
            True,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=3),
            True,
        ),
        (
            datetime.date.today() - datetime.timedelta(days=4),
            False,
        ),
    ],
)
def test_SessionDays_insert_day(
    db_interface,
    date,
    hit,
):
    sessionDay = SessionDay(db_interface)
    id = sessionDay.insert_day(date=date, hit=hit)

    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("SELECT dates, hit FROM {table} WHERE id = %s").format(
                table=sql.Identifier(SessionDay.table_name)
            ),
            [
                id,
            ],
        )
        entries = db.cur.fetchall()
        assert len(entries) == 1
        assert date == entries[0][0]
        assert hit == entries[0][1]
