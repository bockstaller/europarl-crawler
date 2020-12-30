import uuid
from datetime import datetime, timedelta, timezone

import pytest
from psycopg2 import sql

from europarl.db import Request, URLs


def test_table_exists(db_interface):
    request = Request(db_interface)
    assert request.table_exists()


def test_table_not_exists(db_interface):
    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("drop table {table} cascade").format(
                table=sql.Identifier(Request.table_name)
            )
        )

    request = Request(db_interface)
    assert request.table_exists() is False


@pytest.mark.parametrize(
    "status_code",
    [200, 404, 500],
)
@pytest.mark.parametrize(
    "url",
    ["www.internet.de"],
)
@pytest.mark.parametrize(
    "redirected_url",
    ["www.internet1.de"],
)
@pytest.mark.parametrize(
    "requested_at",
    [
        None,
        datetime.now(tz=timezone.utc),
        datetime.now(tz=timezone.utc) + timedelta(hours=1),
        datetime.now(tz=timezone.utc) + timedelta(hours=2),
    ],
)
@pytest.mark.parametrize(
    "document_id",
    [None],
)
def test_Request_mark_as_requested_get_request_log(
    db_interface,
    url,
    status_code,
    redirected_url,
    document_id,
    requested_at,
):
    request = Request(db_interface)
    urls = URLs(db_interface)

    url_id = None
    if url:
        url_id = urls.save_url(None, None, url)

    # TODO: Test document_id

    id = request.mark_as_requested(
        url_id=url_id,
        status_code=status_code,
        redirected_url=redirected_url,
        requested_at=requested_at,
        document_id=document_id,
    )

    assert type(id) == int

    if url:
        assert type(url_id) == int
    else:
        assert url_id is None

    row = request.get_request_log(id)
    assert row[0] == id
    assert row[1] == url_id
    assert row[2] == document_id
    assert row[3] == requested_at
    assert row[4] == status_code
    assert row[5] == redirected_url


def test_get_status_code_summary(db_interface):
    request = Request(db_interface)
    timestamp = []
    now = datetime.now(tz=timezone.utc)

    urls = URLs(db_interface)
    url_id = urls.save_url(None, None, "www.internet.de")

    for i in range(-10, 10):
        ts = now + timedelta(seconds=i)
        timestamp.append(ts)
        request.mark_as_requested(
            url_id=url_id,
            status_code=200,
            redirected_url="www.internet1.de",
            requested_at=ts,
        )

    result = request.get_status_code_summary(timestamp[0], timestamp[-1])
    assert result[200] == 20
    result = request.get_status_code_summary(timestamp[1], timestamp[-2])
    assert result[200] == 18
    result = request.get_status_code_summary(
        timestamp[-1], timestamp[-1] + timedelta(seconds=60)
    )
    assert result[200] == 1
    result = request.get_status_code_summary(
        timestamp[0] - timedelta(seconds=60), timestamp[0]
    )
    assert result[200] == 1
