#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mptools` package."""

import configparser
import logging
import multiprocessing as mp
import os
import signal
import time

import pytest

import europarl.mptools as mptools
from europarl.mptools import (
    MainContext,
    MPQueue,
    Proc,
    ProcWorker,
    QueueProcWorker,
    SignalObject,
    TerminateInterrupt,
    TimerProcWorker,
    _sleep_secs,
    default_signal_handler,
    init_signal,
    proc_worker_wrapper,
    setup_logging,
)


@pytest.fixture()
def mp_config():
    config = configparser.ConfigParser()
    config["Test"] = {"DefaultPollingTimeout": 0.1}
    conf = config["Test"]
    return conf


def test_mpqueue_get():
    Q = MPQueue()

    item = Q.safe_get(None)
    assert item is None

    Q.put("ITEM1")
    Q.put("ITEM2")

    assert Q.safe_get(0.02) == "ITEM1"
    assert Q.safe_get(0.02) == "ITEM2"
    assert Q.safe_get(0.02) is None
    assert Q.safe_get(None) is None

    num_left = Q.safe_close()
    assert num_left == 0


def test_queue_put():
    Q = MPQueue(2)
    assert Q.safe_put("ITEM1")
    assert Q.safe_put("ITEM2")
    assert not Q.safe_put("ITEM3")

    num_left = Q.safe_close()
    assert num_left == 2


def test_drain_queue():
    Q = MPQueue()

    items = list(Q.drain())
    assert items == []

    expected = [f"ITEM{idx}" for idx in range(10)]
    for item in expected:
        Q.put(item)

    items = list(Q.drain())
    assert items == expected

    num_left = Q.safe_close()
    assert num_left == 0


def test_sleep_secs():
    assert _sleep_secs(5.0, time.time() - 1.0) == 0.0
    assert _sleep_secs(1.0, time.time() + 5.0) == 1.0

    end_time = time.time() + 4.0
    got = _sleep_secs(5.0, end_time)
    assert got <= 4.0
    assert got >= 3.7


def test_signal_handling():
    pid = os.getpid()
    evt = mp.Event()
    so = SignalObject(evt)
    init_signal(signal.SIGINT, so, KeyboardInterrupt, default_signal_handler)
    assert not so.shutdown_event.is_set()
    assert so.terminate_called == 0

    os.kill(pid, signal.SIGINT)
    assert so.terminate_called == 1
    assert so.shutdown_event.is_set()

    os.kill(pid, signal.SIGINT)
    assert so.terminate_called == 2
    assert so.shutdown_event.is_set()

    with pytest.raises(KeyboardInterrupt):
        os.kill(pid, signal.SIGINT)

    assert so.terminate_called == 3
    assert so.shutdown_event.is_set()


def test_proc_worker_bad_args(mp_config):
    with pytest.raises(ValueError):
        ProcWorker(
            "TEST",
            1,
            2,
            3,
            4,
            mp_config,
            "ARG1",
            "ARG2",
        )


class ProcWorkerTest(ProcWorker):
    def init_args(self, args):
        self.args = args

    def main_func(self):
        self.logger.info(f"MAIN_FUNC: {self.args}")
        self.shutdown_event.set()


def test_proc_worker_good_args(mp_config):
    logger_q = MPQueue()

    pw = ProcWorkerTest(
        "TEST",
        1,
        2,
        3,
        logger_q,
        mp_config,
        "ARG1",
        "ARG2",
    )
    assert pw.args == ("ARG1", "ARG2")


def test_proc_worker_init_signals(mp_config):
    config = mp_config
    pid = os.getpid()
    evt = mp.Event()
    logger_q = MPQueue()
    pw = ProcWorker("TEST", 1, evt, 3, logger_q, config)
    so = pw.init_signals()

    assert not so.shutdown_event.is_set()
    assert so.terminate_called == 0

    os.kill(pid, signal.SIGINT)
    assert so.terminate_called == 1
    assert so.shutdown_event.is_set()

    os.kill(pid, signal.SIGINT)
    assert so.terminate_called == 2
    assert so.shutdown_event.is_set()

    with pytest.raises(KeyboardInterrupt):
        os.kill(pid, signal.SIGINT)

    assert so.terminate_called == 3
    assert so.shutdown_event.is_set()


def test_proc_worker_no_main_func(caplog, mp_config):
    startup_evt = mp.Event()
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    config = mp_config

    try:
        caplog.set_level(logging.INFO)
        pw = ProcWorker("TEST", startup_evt, shutdown_evt, event_q, logger_q, config)
        with pytest.raises(NotImplementedError):
            pw.main_func()

    finally:
        event_q.safe_close()


def test_proc_worker_run(caplog, mp_config):
    startup_evt = mp.Event()
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    config = mp_config

    caplog.set_level(logging.INFO)
    pw = ProcWorkerTest(
        "TEST", startup_evt, shutdown_evt, event_q, logger_q, config, "ARG1", "ARG2"
    )
    assert not startup_evt.is_set()
    assert not shutdown_evt.is_set()

    pw.run()

    assert startup_evt.is_set()
    assert shutdown_evt.is_set()
    item = event_q.safe_get()
    assert item
    assert item.msg_src == "TEST"
    assert item.msg_type == "SHUTDOWN"
    assert item.msg == "Normal"
    assert "MAIN_FUNC: ('ARG1', 'ARG2')" in caplog.text


def _proc_worker_wrapper_helper(
    caplog,
    worker_class,
    mp_config,
    args=None,
    expect_shutdown_evt=True,
    alarm_secs=1.0,
):
    startup_evt = mp.Event()
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    config = mp_config
    if args is None:
        args = ()

    def alarm_handler(signal_num, current_stack_frame):
        shutdown_evt.set()

    if alarm_secs:
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, alarm_secs)
    caplog.set_level(logging.DEBUG)
    exitcode = proc_worker_wrapper(
        worker_class,
        "TEST",
        startup_evt,
        shutdown_evt,
        event_q,
        logger_q,
        config,
        *args,
    )
    assert startup_evt.is_set()
    assert shutdown_evt.is_set() == expect_shutdown_evt
    items = list(event_q.drain())
    assert items
    last_item = items[-1]
    assert last_item.msg_src == "TEST"
    assert last_item.msg_type == "SHUTDOWN"
    assert last_item.msg == "Normal"
    assert exitcode == 0

    return items[:-1]


def test_proc_worker_wrapper(caplog, mp_config):
    items = _proc_worker_wrapper_helper(
        caplog, ProcWorkerTest, mp_config, ("ARG1", "ARG2")
    )
    assert not items
    assert "MAIN_FUNC: ('ARG1', 'ARG2')" in caplog.text


def test_proc_worker_exception(caplog, mp_config):
    class ProcWorkerException(ProcWorker):
        def main_func(self):
            raise NameError("Because this doesn't happen often")

    startup_evt = mp.Event()
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    config = mp_config

    caplog.set_level(logging.INFO)
    with pytest.raises(SystemExit):
        proc_worker_wrapper(
            ProcWorkerException,
            "TEST",
            startup_evt,
            shutdown_evt,
            event_q,
            logger_q,
            config,
        )
    assert startup_evt.is_set()
    assert not shutdown_evt.is_set()
    item = event_q.safe_get()
    assert item
    assert item.msg_src == "TEST"
    assert item.msg_type == "FATAL"
    assert item.msg == "Because this doesn't happen often"

    assert "Exception Shutdown" in caplog.text


class TimerProcWorkerTest(TimerProcWorker):
    INTERVAL_SECS = 0.01
    times_called = 0

    def main_func(self):
        self.times_called += 1
        self.event_q.put(f"TIMER {self.times_called} [{time.time()}]")
        if self.times_called >= 4:
            self.shutdown_event.set()


def test_timer_proc_worker(caplog, mp_config):
    items = _proc_worker_wrapper_helper(caplog, TimerProcWorkerTest, mp_config)
    assert len(items) == 4
    for idx, item in enumerate(items[:-1]):
        assert item.startswith(f"TIMER {idx + 1} [")


class QueueProcWorkerTest(QueueProcWorker):
    def main_func(self, item):
        self.event_q.put(f"DONE {item}")


def test_queue_proc_worker(caplog, mp_config):
    work_q = MPQueue()
    work_q.put(1)
    work_q.put(2)
    work_q.put(3)
    work_q.put(4)
    work_q.put("END")
    work_q.put(5)

    items = _proc_worker_wrapper_helper(
        caplog,
        QueueProcWorkerTest,
        mp_config,
        args=(work_q,),
        expect_shutdown_evt=False,
    )
    assert len(items) == 4
    assert items == [f"DONE {idx + 1}" for idx in range(4)]


class StartHangWorker(ProcWorker):
    def startup(self):
        while True:
            time.sleep(1.0)


def test_proc_start_hangs(caplog, mp_config):

    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()

    caplog.set_level(logging.INFO)
    Proc.STARTUP_WAIT_SECS = 0.2
    try:
        with pytest.raises(RuntimeError):
            Proc(
                name="TEST",
                worker_class=StartHangWorker,
                shutdown_event=shutdown_evt,
                event_q=event_q,
                logger_q=logger_q,
                config=mp_config,
            )
    finally:
        Proc.STARTUP_WAIT_SECS = 3.0


def test_proc_full_stop(caplog, mp_config):
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    caplog.set_level(logging.INFO)
    proc = Proc(
        name="TEST",
        worker_class=TimerProcWorkerTest,
        shutdown_event=shutdown_evt,
        event_q=event_q,
        logger_q=logger_q,
        config=mp_config,
    )

    for idx in range(4):
        item = event_q.safe_get(1.0)
        assert item, f"idx: {idx}"
        assert item.startswith(f"TIMER {idx + 1} [")

    item = event_q.safe_get(1.0)
    assert item.msg_src == "TEST"
    assert item.msg_type == "SHUTDOWN"
    assert item.msg == "Normal"

    proc.full_stop(wait_time=0.5)

    assert not proc.proc.is_alive()


class NeedTerminateWorker(ProcWorker):
    def main_loop(self):
        while True:
            time.sleep(1.0)


def test_proc_full_stop_need_terminate(caplog, mp_config):
    shutdown_evt = mp.Event()
    event_q = MPQueue()
    logger_q = MPQueue()
    caplog.set_level(logging.INFO)
    proc = Proc(
        name="TEST",
        worker_class=NeedTerminateWorker,
        shutdown_event=shutdown_evt,
        event_q=event_q,
        logger_q=logger_q,
        config=mp_config,
    )
    proc.full_stop(wait_time=0.1)


def test_main_context_stop_queues(config):
    with MainContext(config) as mctx:
        q1 = mctx.MPQueue()
        q1.put("SOMETHING 1")
        q2 = mctx.MPQueue()
        q2.put("SOMETHING 2")

    # -- 3 == the 2 queued items in this test, and the END event
    assert mctx._stopped_queues_result == 3


def _test_stop_procs(cap_log, proc_name, worker_class, config):
    cap_log.set_level(logging.DEBUG)

    with MainContext(config) as mctx:
        mctx.STOP_WAIT_SECS = 0.2
        mctx.Proc(name=proc_name, worker_class=worker_class, config=config["General"])
        time.sleep(0.05)

    print(mctx.STOP_WAIT_SECS)
    for proc in mctx.procs:
        print(proc)
        proc.terminate()
    return mctx._stopped_procs_result, len(mctx.procs)


def test_main_context_exception(config):
    with pytest.raises(ValueError):
        with MainContext(config):
            raise ValueError("Yep, this is a value Error")


class CleanProcWorker(ProcWorker):
    def main_func(self):
        time.sleep(0.001)
        return


def test_main_context_stop_procs_clean(caplog, config):

    (num_failed, num_terminated), num_still_running = _test_stop_procs(
        caplog, "CLEAN", CleanProcWorker, config
    )
    assert num_failed == 0
    assert num_terminated == 0
    assert num_still_running == 0


class FailProcWorker(ProcWorker):
    def main_func(self):
        self.log(logging.DEBUG, "main_func called")
        time.sleep(0.001)
        self.log(logging.DEBUG, "main_func raising")
        raise ValueError("main func value error")


def test_main_context_stop_procs_fail(caplog, config):

    caplog.set_level(logging.DEBUG)
    (num_failed, num_terminated), num_still_running = _test_stop_procs(
        caplog, "FAIL", FailProcWorker, config
    )
    assert num_failed == 1
    assert num_terminated == 0
    assert num_still_running == 0


class HangingProcWorker(ProcWorker):
    def main_loop(self):
        MAX_TERMINATES = 1
        num_terminates = 0
        while num_terminates < MAX_TERMINATES:
            try:
                while True:
                    print(num_terminates)
                    time.sleep(0.02)
            except TerminateInterrupt:
                num_terminates += 1


class HangingProcWorkerHard(ProcWorker):
    def main_loop(self):
        MAX_TERMINATES = 2
        num_terminates = 0
        while num_terminates < MAX_TERMINATES:
            try:
                while True:
                    time.sleep(5.0)
            except TerminateInterrupt:
                num_terminates += 1


def _test_main_context_hang(cap_log, is_hard, config):
    if is_hard:
        return _test_stop_procs(cap_log, "HANG", HangingProcWorkerHard, config)
    else:
        return _test_stop_procs(cap_log, "HANG_Soft", HangingProcWorker, config)


def test_main_context_stop_procs_hung_hard(caplog, config):
    (num_failed, num_terminated), num_still_running = _test_main_context_hang(
        caplog,
        is_hard=True,
        config=config,
    )
    assert num_failed == 0
    assert num_terminated == 0
    assert num_still_running == 1


def test_main_context_stop_procs_hung_soft(caplog, config):
    (num_failed, num_terminated), num_still_running = _test_main_context_hang(
        caplog,
        is_hard=False,
        config=config,
    )
    assert num_failed == 0
    assert num_terminated == 1
    assert num_still_running == 0
