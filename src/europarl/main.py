import datetime
import logging
import multiprocessing
import os
import random
import socket
import sys
import time
from datetime import date
from queue import Full

import requests
from dotenv import load_dotenv
from europarl.db import DBInterface, SessionDay, tables
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.workers import DateUrlGenerator, SessionDayChecker, TokenBucketWorker

DEFAULT_POLLING_TIMEOUT = 0.1
TOKENS_PER_SECOND = 5
MAX_SLEEP_SECS = 0.02


def main():
    # TODO: configure Loglevel with .env
    # TODO: create tables if non-existend

    load_dotenv(override=True)

    db = DBInterface(
        name=os.getenv("EUROPARL_DB_NAME"),
        user=os.getenv("EUROPARL_DB_USER"),
        password=os.getenv("EUROPARL_DB_PASSWORD"),
        host=os.getenv("EUROPARL_DB_HOST"),
        port=os.getenv("EUROPARL_DB_PORT"),
    )

    for table in tables:
        table_inst = table(db)
        if not table_inst.table_exists():
            table_inst.create_table()
        del table_inst

    db.close()

    with MainContext() as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(10)
        url_q = main_ctx.MPQueue(10)

        main_ctx.Proc("TOKEN_GEN_0", TokenBucketWorker, token_bucket_q)
        main_ctx.Proc("SESSION_DAY", SessionDayChecker, token_bucket_q, db)
        main_ctx.Proc("DATE_URL_GEN", DateUrlGenerator, url_q, db)

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


if __name__ == "__main__":
    main()
