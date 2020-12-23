import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from psycopg2 import sql

from europarl.db import URL, Rules, SessionDay, URLs


def test_table_exists(db_interface):
    urls = URLs(db_interface)
    assert urls.table_exists()


def test_table_not_exists(db_interface):
    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("drop table {table} cascade").format(
                table=sql.Identifier(URLs.table_name)
            )
        )

    urls = URLs(db_interface)
    assert urls.table_exists() is False


@pytest.fixture
def sessionDays(db_interface):
    sd = SessionDay(db_interface)
    start = date.today() - timedelta(days=10)
    ids = []
    for i in range(5):
        ids.append(
            sd.update_day(
                date=start + timedelta(days=i),
                status_code=None,
                generated_url=None,
                final_url=None,
                hit=True,
            )
        )
    return ids


names = ["Testrule1", "Testrule2", "Testrule3", "Testrule4", "Testrule5"]


@pytest.fixture
def rules(db_interface):
    r = Rules(db_interface)
    ids = []
    for name in names:
        ids.append(r.register_rule(name))
    return ids


@pytest.fixture
def urls(db_interface, sessionDays, rules):
    urls = []
    for date_id, rule_id, url in zip(sessionDays, rules, names):
        urls.append(URL(date_id, rule_id, url))
    return urls


def test_mark_as_generated(db_interface, urls):
    u = URLs(db_interface)
    result = u.mark_as_generated(urls)
    assert len(urls) == len(result)
    for url in urls:
        assert url.url_id is not None


def test_mark_as_crawled(db_interface, urls):
    u = URLs(db_interface)
    result = u.mark_as_generated(urls)
    assert len(urls) == len(result)
    for url in urls:
        assert url.url_id is not None
        result = u.mark_as_crawled(url)
        assert result is not None


def test_drop_uncrawled(db_interface, urls):
    u = URLs(db_interface)
    result = u.mark_as_generated(urls)
    assert len(urls) == len(result)

    url = urls[0]
    result = u.mark_as_crawled(url)
    assert result is not None

    u.drop_uncrawled_urls()

    update_results = []
    for url in urls:
        update_results.append(u.mark_as_crawled(url))
    print(update_results)
    assert len(update_results) == 5
    assert len([x for x in update_results if x is not None]) == 1


def test_dates_with_less_derived_urls_than_fewer(db_interface, urls):
    u = URLs(db_interface)
    u.mark_as_generated(urls)
    result = u.dates_with_less_derived_urls_than(2, 10)
    assert len(result) == 5


def test_dates_with_less_derived_urls_than_matching(db_interface, urls):
    u = URLs(db_interface)
    u.mark_as_generated(urls)
    result = u.dates_with_less_derived_urls_than(1, 10)
    assert len(result) == 0
