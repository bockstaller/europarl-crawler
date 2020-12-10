from queue import Full

from europarl.db import SessionDay, URLs
from europarl.mptools import ProcWorker


class DateUrlGenerator(ProcWorker):

    PREFETCH_LIMIT = 100

    rules = []

    def init_args(self, args):
        (self.url_q, self.db) = args

    def startup(self):
        super().startup()
        self.sessionDay = SessionDay(self.db)
        self.urls = URLs(self.db)

        self.dates_to_convert = []
        self.derived_urls = []
        self.url = None

    def shutdown(self):
        super().shutdown()
        self.url.drop_uncrawled_urls()

    def apply_rules(self, date):
        return [
            ("a", "b"),
        ]

    def main_func(self):

        if len(self.dates_to_convert) == 0:
            # get all dates which do not have enough derived urls
            self.dates_to_convert = self.urls.dates_with_less_derived_urls_than(
                amount_rules=len(self.rules), limit=self.PREFETCH_LIMIT
            )
            return

        if len(self.derived_urls) == 0:
            date = self.dates_to_convert.pop()
            self.derived_urls = self.apply_rules(date)
            self.urls.mark_as_generated(self.derived_urls)
            return

        if not self.url:
            self.url = self.derived_urls.pop()

        try:
            self.url_q.put(self.url, timeout=self.DEFAULT_POLLING_TIMEOUT)
            self.url = None
        except Full:
            return
