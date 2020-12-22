import configparser
import multiprocessing as mp
import os
from datetime import date, datetime, timedelta, timezone
from queue import Empty
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from europarl.db import DBInterface, Request
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
from europarl.workers import TokenBucketWorker


@pytest.fixture
def tokenbucket_instance(request, db_interface, config):
    # db = db_interface_module

    with MainContext(config) as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(1)
        startup_event = mp.Event()

        return TokenBucketWorker(
            "name",
            startup_event,
            main_ctx.shutdown_event,
            main_ctx.event_queue,
            main_ctx.logger_q,
            main_ctx.config["TokenBucketWorker"],
            token_bucket_q,
        )


def test_startup(tokenbucket_instance):
    tokenbucket_instance.startup()
    assert tokenbucket_instance.last_check is not None
    assert tokenbucket_instance.next_check is not None
    assert tokenbucket_instance.request is not None
    assert tokenbucket_instance.db is not None


@pytest.mark.parametrize(
    "throttling_intervall,last_check,now,next_check,calls",
    [
        (
            10,
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc) + timedelta(seconds=5),
            0,
        ),
        (
            10,
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc) + timedelta(seconds=10),
            datetime.now(tz=timezone.utc) + timedelta(seconds=10),
            0,
        ),
        (
            10,
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc) + timedelta(seconds=11),
            datetime.now(tz=timezone.utc) + timedelta(seconds=10),
            1,
        ),
    ],
)
def test_check_throttling(
    tokenbucket_instance, throttling_intervall, last_check, now, next_check, calls
):
    tokenbucket_instance.startup()

    tokenbucket_instance.THROTTLING_INTERVAL = throttling_intervall

    tokenbucket_instance.request.get_status_code_summary = MagicMock()
    tokenbucket_instance.apply_throttling = MagicMock()

    tokenbucket_instance.last_check = last_check
    tokenbucket_instance.next_check = next_check
    tokenbucket_instance.check_throttling(now)

    assert len(tokenbucket_instance.apply_throttling.mock_calls) == calls
    # the additional call to .keys() increments the call count to 2
    if calls != 0:
        calls += 1
        assert tokenbucket_instance.last_check == now
        assert tokenbucket_instance.next_check == (
            now + timedelta(seconds=throttling_intervall)
        )
    else:
        assert tokenbucket_instance.last_check == last_check
        assert tokenbucket_instance.next_check == next_check

    assert len(tokenbucket_instance.request.get_status_code_summary.mock_calls) == calls


@pytest.mark.parametrize(
    "status_codes, throttling, unthrottling",
    [
        (
            [200],
            0,
            1,
        ),
        (
            [100],
            0,
            1,
        ),
        (
            [300],
            0,
            1,
        ),
        (
            [400],
            0,
            1,
        ),
        (
            [500],
            1,
            0,
        ),
        (
            [408],
            1,
            0,
        ),
        (
            [429],
            1,
            0,
        ),
        (
            [200, 100, 408],
            1,
            0,
        ),
        (
            [200, 100, 500],
            1,
            0,
        ),
    ],
)
def test_apply_throttling(tokenbucket_instance, status_codes, throttling, unthrottling):
    tokenbucket_instance.throttle = MagicMock()
    tokenbucket_instance.unthrottle = MagicMock()
    tokenbucket_instance.apply_throttling(status_codes)
    assert len(tokenbucket_instance.throttle.mock_calls) == throttling
    assert len(tokenbucket_instance.unthrottle.mock_calls) == unthrottling


def test_throttle(tokenbucket_instance):
    tokenbucket_instance.token_bucket_q = MPQueue(11)

    for i in range(20):
        for j in range(10):
            tokenbucket_instance.token_bucket_q.safe_put(j)
        assert tokenbucket_instance.token_bucket_q.safe_get() == 0

        old = tokenbucket_instance.INTERVAL_SECS

        tokenbucket_instance.throttle()

        if i < 16:
            assert tokenbucket_instance.INTERVAL_SECS == 2 * old
        else:
            assert tokenbucket_instance.INTERVAL_SECS == old

        assert tokenbucket_instance.token_bucket_q.empty()


def test_unthrottle(tokenbucket_instance):
    tokenbucket_instance.token_bucket_q = MPQueue(11)

    for i in range(16):
        tokenbucket_instance.throttle()

    assert (
        tokenbucket_instance.INTERVAL_SECS
        == tokenbucket_instance.MIN_INTERVAL_SECS * (2 ** 16)
    )

    for i in range(20):
        old = tokenbucket_instance.INTERVAL_SECS

        tokenbucket_instance.unthrottle()

        if i < 16:
            assert tokenbucket_instance.INTERVAL_SECS == old / 2
        else:
            assert tokenbucket_instance.INTERVAL_SECS == old
