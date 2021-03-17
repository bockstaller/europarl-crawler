import time
from datetime import datetime, timedelta, timezone
from queue import Full

from europarl.db import DBInterface, Rules, SessionDay, URLs
from europarl.mptools import ProcWorker


class DateUrlGenerator(ProcWorker):
    def init_args(self, args):
        (self.url_q,) = args

    def startup(self):
        super().startup()

        self.PREFETCH_LIMIT = int(self.config["PrefetchLimit"])

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.urls = URLs(self.db)
        self.rules = Rules(self.db)

        self.todo_date_rule_combos = []
        self.url_id = None
        self.url_string = None
        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        super().shutdown()

    def get_new_combos(self, limit):
        """
        Get a list of new rule and date combinations

        Args:
            limit (int): amount of combinations that should be retrieved

        Returns:
            list: list of combination dictionaries
        """
        self.logger.debug("Getting new date/rule-combinations")

        combos = self.urls.get_todo_rule_and_date_combos(limit=limit)

        # got no new combinations from db. sleep for the polling timeout before retrying
        if len(combos) == 0:
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
        else:
            self.logger.info(
                "Got {} new combinations from database".format(len(combos))
            )

        return combos

    def create_url(self, combo):
        """
        Creates a url based upon a rule and date combination

        Args:
            combo (dict): rule and date combination dictionary

        Returns:
            tuple: url_id and url_string
        """
        self.logger.debug(
            "Applying rule: {} to date: {}".format(combo["rulename"], combo["date"])
        )
        url_id, url_string = self.rules.apply_rule(
            date_id=combo["date_id"], rule_id=combo["rule_id"]
        )
        self.logger.debug("Result: {}".format(url_string))
        return url_id, url_string

    def enqueue_url(self, url_id, url_string):
        """
        Queues up a URl

        Args:
            url_id (int): id of the url
            url_string (id): url string

        Returns:
            tuple of url_id and url_string: values are None if the value was enqueued successfully, the old values stay if this isn't the case
        """
        try:
            self.logger.debug("Queueing up URL with id: {}".format(url_id))
            self.url_q.put(url_id, timeout=self.DEFAULT_POLLING_TIMEOUT)
            self.logger.info("Queued up URL: {} with id: {}".format(url_string, url_id))
            url_string, url_id = None, None
        except Full:
            pass

        return url_id, url_string

    def main_func(self):
        """
        Continuously enqueue new urls.
        First block sets up a buffer of date and rule combinations.
        This buffer is then iteratively consumed with every iteration, urls created, stored and enqueued
        """

        if len(self.todo_date_rule_combos) == 0:
            self.todo_date_rule_combos = self.get_new_combos(limit=self.PREFETCH_LIMIT)
            if len(self.todo_date_rule_combos) == 0:
                time.sleep(self.DEFAULT_POLLING_TIMEOUT * 10)

            return

        if self.url_id is None:
            self.url_id, self.url_string = self.create_url(
                combo=self.todo_date_rule_combos.pop()
            )

        self.url_id, self.url_string = self.enqueue_url(
            url_id=self.url_id, url_string=self.url_string
        )
