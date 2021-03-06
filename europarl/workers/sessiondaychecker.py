import logging
import time
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests

from europarl.db import DBInterface, Request, Rules, SessionDay
from europarl.mptools import QueueProcWorker
from europarl.rules.protocol import SessionDayRule


class SessionDayChecker(QueueProcWorker):

    PREFETCH_LIMIT = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dates_to_check = []

    def init_args(self, args):
        (self.work_q,) = args

    def startup(self):
        """
        Initializes a sessionDay-table instance and a long running requests-session object which will handle all outgoing requests
        """
        super().startup()

        self.PREFETCH_LIMIT = int(self.config["PrefetchLimit"])

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.sessionDay = SessionDay(self.db)
        self.request = Request(self.db)
        self.rules = Rules(self.db)

        self.session = requests.Session()

        self.url, self.url_id = None, None

        self.sleep_end = datetime.now(timezone.utc) - timedelta(hours=1)

        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        """
        Cleans up by closing the requests-session and deleting the
        sessionDay which will close the database connection
        """
        super().shutdown()
        self.session.close()
        del self.sessionDay

    def check_for_sleep(self, current_time, sleep_end):
        """
        This function determines if the main function is still sleeping
        We don't want to hammer the database with request every 100ms, querying
        if a new day has started. This function checks if a sleeping time window is over. This information can be used to return the main function early or continue computing.

        We don't want to block and time.sleep() for the duration of the sleep.
        This would block and make the process not responsive to the quit signal.

        Args:
            current_time (datetime): current execution timestamp
            delta (timedelta): sleeping duration

        Returns:
            boolean: still sleeping?
        """

        self.logger.debug("Checking if sleep time is currently active")
        self.logger.debug("Sleep time is over at: {}".format(sleep_end))
        if current_time < sleep_end:
            self.logger.debug("Current time is: {} - Aborting".format(current_time))
            return True
        self.logger.debug("Current time is: {} - Continuing".format(current_time))
        return False

    def get_new_date(self):
        try:
            return self.dates_to_check.pop()
        except IndexError:
            self.logger.debug("Querying database for sessions to check")
            dates = self.sessionDay.get_unchecked_days(self.PREFETCH_LIMIT)
            self.logger.debug("Database returned the following dates: {}".format(dates))
            if len(dates) > 0:
                self.dates_to_check = dates
                return self.dates_to_check.pop()
            else:
                self.logger.debug(
                    "Database returned no value, initializing sleep: {}".format(dates)
                )
                self.set_sleep(timedelta(minutes=1))
                return None

    def crawl(self, session, date):
        """
        Generates a url to crawls based upon the passed in
        date and then crawls it.
        It will return the status code and if crawling the url
        was a hit or miss. Additionally it will return the
        generated document_url and the final url after following
        all redirects

        Args:
            session (requests.session): long running session object
            date (datetime.date): date to generate the url from

        Returns:
            Tuple(hit, status_code, generated_url, final_url)
        """

        if self.url is None:
            date_id = self.sessionDay.insert_date(date)
            rule = self.rules.get_rule(rulename=SessionDayRule.name)
            # construct url to crawl
            self.url_id, self.url = self.rules.apply_rule(
                rule_id=rule[0], date_id=date_id
            )

        self.logger.debug("Crawling url: {}".format(self.url))

        try:
            resp = self.session.head(self.url, allow_redirects=True)

            self.request.mark_as_requested(
                url_id=self.url_id,
                status_code=resp.status_code,
                redirected_url=resp.url,
            )
            self.logger.debug("Server response: {}".format(resp.status_code))

            if resp.status_code == 200:
                self.logger.info("Identified session on the: {}".format(date))

            if resp.status_code == 404:
                self.logger.info("Identified no session on the: {}".format(date))

            self.url, self.url_id = None, None

        except requests.ReadTimeout as e:

            self.logger.warn("Timeout for url: {}".format(self.url))
            self.logger.warn("Exception Message: {}".format(e))

            self.request.mark_as_requested(
                url_id=self.url_id, status_code=408, redirected_url=self.url
            )
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
            return

        except requests.RequestException as e:
            self.logger.warn("Request exception for url: {}".format(self.url))
            self.logger.warn("Exception Message: {}".format(e))
            self.request.mark_as_requested(
                url_id=self.url_id, status_code=460, redirected_url=self.url
            )
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
            return

    def set_sleep(self, delta):
        """
        Sets the sleep timer for the sessiondaychecker

        Args:
            delta (datetime.timedelta): Time to sleep
        """
        self.logger.debug("Setting sleep (next iteration) for: {}".format(delta))
        self.sleep_end = datetime.now(tz=timezone.utc) + delta

    def main_func(self, token):

        # check if function should return early because it is still sleeping
        if self.check_for_sleep(
            current_time=datetime.now(timezone.utc), sleep_end=self.sleep_end
        ):
            self.logger.debug("Returning token to bucket")
            # put "consumed token back on queue, because no crawling work was done"
            try:
                self.work_q.put(token, timeout=self.DEFAULT_POLLING_TIMEOUT)
            except Full:
                pass
            self.logger.debug("Still sleeping, Returned Token to Bucket")
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
            return

        # get a date value to operate on and start sleeping cycle if db doesn't return a value
        date = self.get_new_date()
        if date is not None:
            self.logger.debug("Checking date: {}".format(date))
        else:
            self.logger.debug("Database returned no unchecked dates, Retrying")
            return

        self.crawl(self.session, date)
