import uuid
from datetime import datetime, timedelta, timezone

import pytest
from psycopg2 import sql

from europarl.db import URL, Request, URLs


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
    "requested_url",
    ["www.internet.de"],
)
@pytest.mark.parametrize(
    "final_url",
    ["www.internet1.de"],
)
@pytest.mark.parametrize(
    "requested_at",
    [
        datetime.now(tz=timezone.utc),
        datetime.now(tz=timezone.utc) + timedelta(hours=1),
        datetime.now(tz=timezone.utc) + timedelta(hours=2),
    ],
)
@pytest.mark.parametrize(
    "content_uuid",
    [str(uuid.uuid4())],
)
@pytest.mark.parametrize(
    "url",
    [False, True],
)
def test_Request_mark_as_requested_get_request_log(
    db_interface,
    status_code,
    requested_url,
    final_url,
    requested_at,
    content_uuid,
    url,
):
    request = Request(db_interface)
    url = URLs(db_interface)

    url_id = None
    if url:
        url_inst = URL(None, None, requested_url)
        url_inst = url.mark_as_generated([url_inst])[0]
        url_id = url_inst.url_id

    id = request.mark_as_requested(
        status_code=status_code,
        requested_url=requested_url,
        final_url=final_url,
        requested_at=requested_at,
        content_uuid=content_uuid,
        url_id=url_id,
    )

    assert type(id) == int

    if url:
        assert type(url_id) == int
    else:
        assert url_id is None

    row = request.get_request_log(id)
    assert row[0] == status_code
    assert row[1] == requested_url
    assert row[2] == final_url
    assert row[3] == requested_at
    assert row[4] == content_uuid
    assert row[5] == url_id
