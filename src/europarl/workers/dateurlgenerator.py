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
        print(date)
        for rule in self.rules:
            urls.append(rule.get_url(date))
        return urls

    def main_func(self):

        if len(self.derived_urls) == 0:
            try:
                date = self.urls.dates_with_less_derived_urls_than(
                    amount_rules=len(self.rules), limit=1
                )[0]
            except IndexError:
                time.sleep(self.DEFAULT_POLLING_TIMEOUT)
                return

            self.derived_urls = self.apply_rules(date)
            assert len(self.derived_urls) == len(self.rules)
            self.urls.mark_as_generated(self.derived_urls)
            return

        try:
            if not self.url:
                self.url = self.derived_urls.pop()
            self.url_q.put(self.url, timeout=self.DEFAULT_POLLING_TIMEOUT)
            self.logger.info("Queued up url:{}".format(self.url.url))
            self.url = None
        except Full:
            return
