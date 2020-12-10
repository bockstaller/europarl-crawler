import datetime

import pytest
from europarl.db import SessionDay
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
    "date, hit, status_code, checked, generated_url, final_url",
    [
        (
            datetime.date.today() - datetime.timedelta(days=0),
            False,
            404,
            False,
            "www.test.de",
            "www.test1.de",
        ),
        (
            datetime.date.today() - datetime.timedelta(days=1),
            False,
            404,
            True,
            "www.test.de",
            "www.test1.de",
        ),
        (
            datetime.date.today() - datetime.timedelta(days=2),
            True,
            200,
            False,
            "www.test.de",
            "www.test1.de",
        ),
        (
            datetime.date.today() - datetime.timedelta(days=3),
            True,
            200,
            True,
            "www.test.de",
            "www.test1.de",
        ),
        (
            datetime.date.today() - datetime.timedelta(days=4),
            False,
            404,
            False,
            "www.test.de",
            "www.test1.de",
        ),
    ],
)
def test_SessionDays_update_day_insert(
    db_interface, date, hit, status_code, checked, generated_url, final_url
):
    sessionDay = SessionDay(db_interface)
    id = sessionDay.update_day(
        date=date,
        status_code=status_code,
        hit=hit,
        checked=checked,
        generated_url=generated_url,
        final_url=final_url,
    )

    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL(
                "SELECT dates, hit, status_code, checked, checked_at,  generated_url, final_url FROM {table} WHERE id = %s"
            ).format(table=sql.Identifier(SessionDay.table_name)),
            [
                id,
            ],
        )
        entries = db.cur.fetchall()
        assert len(entries) == 1
        assert date == entries[0][0]
        assert hit == entries[0][1]
        assert status_code == entries[0][2]
        assert checked == entries[0][3]
        assert entries[0][4] is not None
        assert entries[0][5] == generated_url
        assert entries[0][6] == final_url


def test_SessionDays_update_day_upsert(db_interface):
    sessionDay = SessionDay(db_interface)
    date = datetime.date.today()
    id = sessionDay.update_day(
        date=date,
        status_code=200,
        hit=False,
        checked=False,
        generated_url="www.test.de",
        final_url="www.test1.de",
    )

    ts = None

    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("SELECT dates, checked_at FROM {table} WHERE id = %s").format(
                table=sql.Identifier(SessionDay.table_name)
            ),
            [
                id,
            ],
        )
        entries = db.cur.fetchall()
        assert len(entries) == 1
        assert date == entries[0][0]
        ts = entries[0][1]

    id = sessionDay.update_day(
        date=date,
        status_code=200,
        hit=False,
        checked=False,
        generated_url="www.test.de",
        final_url="www.test1.de",
    )
    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("SELECT dates, checked_at FROM {table} WHERE id = %s").format(
                table=sql.Identifier(SessionDay.table_name)
            ),
            [
                id,
            ],
        )
        entries = db.cur.fetchall()
        assert len(entries) == 1
        assert date == entries[0][0]
        assert ts != entries[0][1]
