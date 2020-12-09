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
from europarl.db import DBInterface, SessionDay
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.workers import SessionDayChecker, TokenBucketWorker

DEFAULT_POLLING_TIMEOUT = 0.1
MAX_SLEEP_SECS = 0.02


def main():
    # TODO: configure Loglevel with .env

    load_dotenv(override=True)

    db = DBInterface(
        name=os.getenv("EUROPARL_DB_NAME"),
        user=os.getenv("EUROPARL_DB_USER"),
        password=os.getenv("EUROPARL_DB_PASSWORD"),
        host=os.getenv("EUROPARL_DB_HOST"),
        port=os.getenv("EUROPARL_DB_PORT"),
    )

    with MainContext() as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(200)

        main_ctx.Proc("TOKEN_GEN_0", TokenBucketWorker, token_bucket_q)
        main_ctx.Proc("SESSION_DAY", SessionDayChecker, token_bucket_q, db)

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


if __name__ == "__main__":
    main()
