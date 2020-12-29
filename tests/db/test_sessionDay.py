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
    "date",
    [
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.date.today() - datetime.timedelta(days=0),
        datetime.date.today() - datetime.timedelta(days=2),
        datetime.date.today() - datetime.timedelta(days=3),
        datetime.date.today() - datetime.timedelta(days=4),
    ],
)
def test_SessionDays_insert_day(
    db_interface,
    date,
):
    sessionDay = SessionDay(db_interface)
    id = sessionDay.insert_date(date=date)

    get_id, get_date = sessionDay.get_date(id)

    assert get_id == id
    assert get_date == date
