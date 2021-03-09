import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from psycopg2 import sql

from europarl.db import Request, Rules, SessionDay, URLs
from europarl.rules.rule import rule_registry


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
            sd.insert_date(
                date=start + timedelta(days=i),
            )
        )
    return ids


@pytest.fixture
def rulesFix(db_interface):
    r = Rules(db_interface)
    ids = []

    ids = r.register_rules(rule_registry.all)
    return ids


def test_save_url_completly_unique(db_interface, sessionDays, rulesFix):
    u = URLs(db_interface)
    result = []
    for day_id, rule_id in zip(sessionDays, rulesFix):
        result.append(
            u.save_url(
                date_id=day_id, rule_id=rule_id, url="www.internet.de" + str(day_id)
            )
        )
    entries = list(zip(sessionDays, rulesFix))
    assert len(entries) == len(result)


def test_save_url_rule_unique(db_interface, sessionDays, rulesFix):
    """
    Only the combination of url and responsible rule should be unique. This allows for the same url being generated by the session_day_checker and by the date_url_generator, given that the session_day-rule wraps the
    """
    u = URLs(db_interface)
    result = []
    for day_id, rule_id in zip(sessionDays, rulesFix):
        result.append(
            u.save_url(date_id=day_id, rule_id=rule_id, url="www.internet.de")
        )
    entries = list(zip(sessionDays, rulesFix))
    assert len(entries) == len(result)


@pytest.fixture
def todo_setup(db_interface):
    u = URLs(db_interface)
    r = Request(db_interface)
    ru = Rules(db_interface)
    s = SessionDay(db_interface)

    day_id = s.insert_date(date.today())
    rule_ids = ru.register_rules(rule_registry.all)
    session_url_id = u.save_url(
        date_id=day_id, rule_id=rule_ids[0], url="www.internet.de"
    )
    r.mark_as_requested(
        url_id=session_url_id, status_code=200, redirected_url="www.internet1.de"
    )

    return {"day_id": day_id, "rule_ids": rule_ids, "session_url_id": session_url_id}


def test_get_todo_rule_and_date_combos_nothing(db_interface, todo_setup):
    # valid session url is found but no rule is activated
    u = URLs(db_interface)
    ret = u.get_todo_rule_and_date_combos(limit=100)
    assert len(ret) == 0


def test_get_todo_rule_and_date_combos_one_rule(db_interface, todo_setup):
    # valid session url is found and one rule is activated
    u = URLs(db_interface)
    ru = Rules(db_interface)
    s = SessionDay(db_interface)
    ru.update_rule_state(id=todo_setup["rule_ids"][1], active=True)
    ret = u.get_todo_rule_and_date_combos(limit=100)
    assert len(ret) == 1
    assert ret[0]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[0]["rulename"] == list(rule_registry.all.keys())[1]


def test_get_todo_rule_and_date_combos_two_rules(db_interface, todo_setup):
    # valid session url is found and two rules are activated
    u = URLs(db_interface)
    ru = Rules(db_interface)
    s = SessionDay(db_interface)
    ru.update_rule_state(id=todo_setup["rule_ids"][1], active=True)
    ru.update_rule_state(id=todo_setup["rule_ids"][2], active=True)

    ret = u.get_todo_rule_and_date_combos(limit=100)
    assert len(ret) == 2
    assert ret[0]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[0]["rulename"] == list(rule_registry.all.keys())[1]
    assert ret[1]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[1]["rulename"] == list(rule_registry.all.keys())[2]


def test_get_todo_rule_and_date_combos_three_rules(db_interface, todo_setup):
    # valid session url is found and three rules are activated
    u = URLs(db_interface)
    ru = Rules(db_interface)
    s = SessionDay(db_interface)
    ru.update_rule_state(id=todo_setup["rule_ids"][1], active=True)
    ru.update_rule_state(id=todo_setup["rule_ids"][2], active=True)
    ru.update_rule_state(id=todo_setup["rule_ids"][3], active=True)
    ret = u.get_todo_rule_and_date_combos(limit=100)
    assert len(ret) == 3
    assert ret[0]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[0]["rulename"] == list(rule_registry.all.keys())[1]
    assert ret[1]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[1]["rulename"] == list(rule_registry.all.keys())[2]
    assert ret[2]["date"] == s.get_date(todo_setup["day_id"])[1]
    assert ret[2]["rulename"] == list(rule_registry.all.keys())[3]


def count_urls(db_interface):
    with db_interface.cursor() as db:
        query = """ SELECT COUNT(*)
                    FROM urls;
                """
        db.cur.execute(query)
        count = db.cur.fetchone()[0]
    return count


@pytest.fixture
def url_ids(db_interface):
    u = URLs(db_interface)

    url_ids = []
    amount = 10
    for i in range(amount):
        url_ids.append(u.save_url(None, None, str(i)))

    assert count_urls(db_interface) == amount
    return url_ids


def test_drop_uncrawled_urls_drop_all(db_interface, url_ids):
    u = URLs(db_interface)

    u.drop_uncrawled_urls()

    assert count_urls(db_interface) == 0


def test_drop_uncrawled_urls_drop_all_but_one(db_interface, url_ids):
    u = URLs(db_interface)
    r = Request(db_interface)

    r.mark_as_requested(url_ids[0], 200, "wwww.internet.de")

    u.drop_uncrawled_urls()

    assert count_urls(db_interface) == 1


def test_drop_uncrawled_urls_drop_all_but_two(db_interface, url_ids):
    u = URLs(db_interface)
    r = Request(db_interface)

    r.mark_as_requested(url_ids[0], 200, "wwww.internet.de")
    r.mark_as_requested(url_ids[1], 200, "wwww.internet.de")

    u.drop_uncrawled_urls()

    assert count_urls(db_interface) == 2
