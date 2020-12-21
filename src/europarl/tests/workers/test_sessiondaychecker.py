import configparser
import multiprocessing as mp
import os
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from europarl.db.interface import DBInterface
from europarl.mptools import (
    EventMessage,
    MainContext,
    MPQueue,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.workers import SessionDayChecker


@pytest.fixture
def config():
    # TODO modify settings.ini to use in tests
    config = configparser.ConfigParser()
    config.read("settings.ini")
    return config


@pytest.fixture
def sessiondaychecker_instance(request, db_interface, config):
    # db = db_interface

    with MainContext(config) as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(1)

        return SessionDayChecker(
            "name",
            mp.Event(),
            main_ctx.shutdown_event,
            main_ctx.event_queue,
            main_ctx.logger_q,
            main_ctx.config["SessionDayChecker"],
            token_bucket_q,
        )


@pytest.mark.parametrize(
    "current_time,sleep_end,expected",
    [
        (
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc) + timedelta(minutes=1),
            True,
        ),
        (
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc) - timedelta(minutes=1),
            False,
        ),
    ],
)
def test_check_for_sleep(sessiondaychecker_instance, current_time, sleep_end, expected):
    assert (
        sessiondaychecker_instance.check_for_sleep(current_time, sleep_end) is expected
    )


def test_get_new_date(sessiondaychecker_instance):
    sd = sessiondaychecker_instance

    days = []
    start = date.today()
    for i in range(10):
        days.append(start + timedelta(days=i))

    sd.dates_to_check = days

    for i in range(9, 1):
        sd.get_new_date()
        assert len(sd.dates_to_check) == i


def test_get_new_date_from_database_magicmock(sessiondaychecker_instance):
    sd = sessiondaychecker_instance
    sd.PREFETCH_LIMIT = 10
    sd.startup()

    def mock_get_unchecked_days(limit):
        days = []
        start = date.today()
        for i in range(limit):
            days.append(start + timedelta(days=i))
        return days

    sd.sessionDay.get_unchecked_days = MagicMock(side_effect=mock_get_unchecked_days)

    sd.dates_to_check = []

    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 0

    sd.get_new_date()

    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 1

    for i in reversed(range(1, 10)):
        assert len(sd.dates_to_check) == i
        sd.get_new_date()

    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 1

    sd.get_new_date()

    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 2


def test_get_new_date_from_database_empty_db(sessiondaychecker_instance):
    sd = sessiondaychecker_instance
    sd.PREFETCH_LIMIT = 10
    sd.startup()

    sd.dates_to_check = []

    sd.sessionDay.get_unchecked_days = MagicMock(return_value=[])
    sd.set_sleep = Mock()

    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 0
    sd.get_new_date()
    assert len(sd.sessionDay.get_unchecked_days.mock_calls) == 1
    assert len(sd.dates_to_check) == 0

    assert len(sd.set_sleep.mock_calls) == 1


def test_set_sleep(sessiondaychecker_instance):
    sd = sessiondaychecker_instance
    sd.startup()
    start_sleep_end = sd.sleep_end
    delta = timedelta(minutes=1)
    sd.set_sleep(delta=delta)
    assert sd.sleep_end > start_sleep_end


@pytest.mark.parametrize(
    "status_code,sleep_set",
    [
        (
            200,
            False,
        ),
        (
            408,
            True,
        ),
        (
            429,
            True,
        ),
        (
            500,
            True,
        ),
        (
            501,
            True,
        ),
    ],
)
def test_crawl(sessiondaychecker_instance, status_code, sleep_set):
    sd = sessiondaychecker_instance
    sd.startup()

    sd.session.head = Mock(
        return_value=SimpleNamespace(
            **{"status_code": status_code, "url": "www.internet.de"}
        )
    )

    hit, ret_status_code, document_url, real_url = sd.crawl(
        sd.session, date(year=2020, month=12, day=10)
    )

    assert len(sd.session.head.mock_calls) == 1
    assert (sd.sleep_end > datetime.now(tz=timezone.utc)) == sleep_set

    assert hit != sleep_set
    assert ret_status_code == status_code
    assert (
        document_url
        == "https://europarl.europa.eu/doceo/document/PV-9-2020-12-10_EN.pdf"
    )
    assert real_url == "www.internet.de"
