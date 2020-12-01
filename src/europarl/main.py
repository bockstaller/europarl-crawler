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
from europarl.db.interface import DBInterface
from europarl.db.tables import SessionDay
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)

DEFAULT_POLLING_TIMEOUT = 0.1
MAX_SLEEP_SECS = 0.02


class TokenBucketWorker(TimerProcWorker):
    """
    Creates tokens for the crawlers to use and enques them in the bucket queue which must be passed as an arg-

    """

    INTERVAL_SECS = 0.01

    token_nr = 0

    def init_args(self, args):
        (self.token_bucket_q,) = args

    def main_func(self):
        """
        The token-string carries no meaning and is only intended for debugging purposes.
        The continous creating, waiting and discarding loop in case of a full token_bucket_q keeps the process responsive to shutdown signals which are handled in the base class TimerProcWorker.
        """

        token = "{}:{:04d}".format(self.name, self.token_nr)
        self.logger.debug("Created token: {}".format(token))

        self.logger.debug("Enqueing token: {}".format(token))

        try:
            self.token_bucket_q.put(token, timeout=DEFAULT_POLLING_TIMEOUT)
            self.logger.info("Enqueued token: {}".format(token))
        except Full:
            self.logger.debug("Queue full. - Discarding token: {}".format(token))
            return

        if self.token_nr >= 1000:
            self.token_nr = 0
            self.logger.debug("Token number overflow. Reseted to 0")
        else:
            self.token_nr += 1
            self.logger.debug("Incremented token number to {}".format(self.token_nr))


class SessionDayChecker(QueueProcWorker):
    BASE_URL = "https://europarl.europa.eu/doceo/document/"
    PREFETCH_LIMIT = 100
    dates_to_check = []

    terms = {
        "4": [date(1994, 7, 1), date(1999, 7, 31)],
        "5": [date(1999, 7, 1), date(2004, 7, 31)],
        "6": [date(2004, 7, 1), date(2009, 7, 31)],
        "7": [date(2009, 7, 1), date(2014, 7, 31)],
        "8": [date(2014, 7, 1), date(2019, 7, 31)],
        "9": [date(2019, 7, 1), date(2024, 7, 31)],
    }

    def init_args(self, args):
        self.logger.log(logging.DEBUG, f"Entering QueueProcWorker.init_args : {args}")
        (
            self.work_q,
            self.db,
        ) = args

    def startup(self):
        self.sessionDay = SessionDay(self.db)

        self.session = requests.Session()
        pass

    def shutdown(self):
        self.session.close()

        pass

    def get_term(self, date):
        for key, term in self.terms.items():
            if term[0] < date < term[1]:
                return key

    def main_func(self, token):
        try:
            date = self.dates_to_check.pop()
        except IndexError:
            self.logger.debug("Querying database for sessions to check")
            dates = self.sessionDay.get_unchecked_days(self.PREFETCH_LIMIT)
            self.logger.debug("Database returned the following dates: {}".format(dates))
            self.dates_to_check = dates

            date = self.dates_to_check.pop()

        self.logger.info("Checking date: {}".format(date))

        document_url = (
            self.BASE_URL
            + "PV-"
            + self.get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "_EN"
            + ".pdf"
        )

        self.logger.debug("Crawling url: {}".format(document_url))
        resp = self.session.head(document_url, allow_redirects=True)
        self.logger.debug("Server response: {}".format(resp.status_code))

        hit = resp.status_code == 200

        try:
            self.logger.debug("Storing result")
            self.sessionDay.update_day(date, hit)
            self.logger.info("Stored result. Date: {}; Hit: {};".format(date, hit))
        except Exception:
            self.logger.error("Couldn't store result for date: {}".format(date))


def main():

    load_dotenv(override=True)

    db = DBInterface(
        os.getenv("EUROPARL_DB_NAME"),
        os.getenv("EUROPARL_DB_USER"),
        os.getenv("EUROPARL_DB_PASSWORD"),
        os.getenv("EUROPARL_DB_HOST"),
        os.getenv("EUROPARL_DB_PORT"),
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
