import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests
from europarl.db import Request
from europarl.db.url import URL, URLs
from europarl.mptools import QueueProcWorker
from europarl.rules import PdfProtocol


class DocumentDownloader(QueueProcWorker):

    DEFAULT_POLLING_TIMEOUT = 0.2
    PATH = "../data/"

    def init_args(self, args):
        self.logger.log(logging.DEBUG, f"Entering QueueProcWorker.init_args : {args}")
        (
            self.work_q,
            self.url_q,
            self.db,
        ) = args

    def startup(self):
        """"""
        self.db.connection_name = self.db.connection_name + " - DocumentDownloader"
        self.request = Request(self.db)
        self.url = URLs(self.db)
        self.session = requests.Session()

    def shutdown(self):
        """"""
        self.session.close()
        del self.request

    def main_func(self, token):
        # get url
        url_obj = self.url_q.safe_get()

        if url_obj:
            # make request
            resp = self.session.get(url_obj.url, allow_redirects=True)

            # if successfull store file
            if resp.status_code == 200:
                generated_uuid = uuid.uuid4()
                open(self.PATH + str(generated_uuid) + url_obj.file_ending, "wb").write(
                    resp.content
                )

            # store crawling result in crawling table
            self.request.mark_as_requested(
                status_code=resp.status_code,
                requested_url=url_obj.url,
                final_url=resp.url,
                content_uuid=str(generated_uuid),
                url_id=url_obj.url_id,
            )

            self.url.mark_as_crawled(url_obj)
