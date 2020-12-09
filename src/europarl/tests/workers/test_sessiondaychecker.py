import multiprocessing as mp
import os
from datetime import date, datetime, timedelta, timezone

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
def sessiondaychecker_instance(request):
    db = DBInterface(
        name="test",
        user=os.getenv("EUROPARL_DB_USER"),
        password=os.getenv("EUROPARL_DB_PASSWORD"),
        host=os.getenv("EUROPARL_DB_HOST"),
        port=os.getenv("EUROPARL_DB_PORT"),
    )

    with MainContext() as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(1)

        return SessionDayChecker(
            "name",
            mp.Event(),
            main_ctx.shutdown_event,
            main_ctx.event_queue,
            token_bucket_q,
            main_ctx.logger_q,
            db,
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


@pytest.mark.parametrize(
    "date,expected",
    [
        (date(year=2019, month=8, day=1), "9"),
        (date(year=2014, month=8, day=1), "8"),
        (date(year=2009, month=8, day=1), "7"),
        (date(year=2004, month=8, day=1), "6"),
        (date(year=1999, month=8, day=1), "5"),
        (date(year=1994, month=8, day=1), "4"),
        (date(year=1989, month=8, day=1), "3"),
        (date(year=1984, month=8, day=1), "2"),
        (date(year=1979, month=8, day=1), "1"),
        (date(year=1950, month=8, day=1), "0"),
        (date(year=2025, month=8, day=1), "0"),
    ],
)
def test_get_term(sessiondaychecker_instance, date, expected):
    assert sessiondaychecker_instance.get_term(date) == expected
