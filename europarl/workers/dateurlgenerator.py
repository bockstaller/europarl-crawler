import time
from queue import Full

from europarl.db import DBInterface, SessionDay, URLs
from europarl.mptools import ProcWorker
from europarl.rules import HtmlProtocol, PdfProtocol


class DateUrlGenerator(ProcWorker):
    DEFAULT_POLLING_TIMEOUT = 0.2

    def init_args(self, args):
        (self.url_q,) = args

    def startup(self):
        super().startup()

        self.db = DBInterface(
            name=self.config["dbname"],
            user=self.config["dbuser"],
            password=self.config["dbpassword"],
            host=self.config["dbhost"],
            port=self.config["dbport"],
        )

        self.db.connection_name = self.name

        self.urls = URLs(self.db)

        rules = [HtmlProtocol, PdfProtocol]

        self.rules = []
        for rule in rules:
            inst = rule()
            inst.register(self.db)
            self.rules.append(inst)

        self.dates_to_convert = []
        self.derived_urls = []
        self.url = None

    def shutdown(self):
        super().shutdown()
        self.urls.drop_uncrawled_urls()

    def apply_rules(self, date):
        urls = []
        for rule in self.rules:
            new_url = rule.get_url(date)
            urls.append(new_url)
            self.logger.debug("Appended url: {}".format(new_url))
        return urls

    def main_func(self):

        if len(self.derived_urls) == 0:
            self.logger.debug("Getting new date")
            try:
                date = self.urls.dates_with_less_derived_urls_than(
                    amount_rules=len(self.rules), limit=1
                )[0]
                self.logger.debug("Got date {} from database".format(date))
            except IndexError:
                time.sleep(self.DEFAULT_POLLING_TIMEOUT)
                self.logger.debug("Got no new URL from database")
                return

            self.logger.info("Deriving URLs for date: {}".format(date))
            self.derived_urls = self.apply_rules(date)
            self.logger.debug(
                "Derived the following URLs: {}".format(self.derived_urls)
            )
            self.urls.mark_as_generated(self.derived_urls)
            self.logger.debug("Marked derived urls as generated.")
            return

        try:
            if not self.url:
                self.logger.debug("Getting new url to queue up")
                self.url = self.derived_urls.pop()
            self.logger.debug("Queueing up URL: {}".format(self.url))
            self.url_q.put(self.url, timeout=self.DEFAULT_POLLING_TIMEOUT)
            self.logger.info("Queued up url: {}".format(self.url.url))
            self.url = None
        except Full:
            return
