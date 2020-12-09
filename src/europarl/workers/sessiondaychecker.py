import logging
from datetime import date

import requests
from europarl.db import SessionDay
from europarl.mptools import QueueProcWorker


class SessionDayChecker(QueueProcWorker):
    # TODO: Explicitly handle 200s, 404s and other errors and store these results in the db
    # TODO: Handle no work left case
    # TODO: Improve logging
    # TODO: break main_func into smaller functions
    # TODO: add tests
    # TODO: document

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
        return "0"

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
            self.sessionDay.update_day(date, hit, True)
            self.logger.info("Stored result. Date: {}; Hit: {};".format(date, hit))
        except Exception:
            self.logger.error("Couldn't store result for date: {}".format(date))
