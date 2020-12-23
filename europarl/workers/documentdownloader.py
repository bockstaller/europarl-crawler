import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests

from europarl.db import DBInterface, Request
from europarl.db.url import URL, URLs
from europarl.mptools import QueueProcWorker
from europarl.rules import PdfProtocol


class DocumentDownloader(QueueProcWorker):

    PATH = "../data/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_obj = None

    def init_args(self, args):
        (
            self.work_q,
            self.url_q,
        ) = args

    def startup(self):
        """"""
        super().startup()

        self.PATH = self.config["Path"]

        self.db = DBInterface(self.config)
        self.db.connection_name = self.name

        self.request = Request(self.db)
        self.url = URLs(self.db)

    def shutdown(self):
        """"""
        super().shutdown()

        del self.request

    def main_func(self, token):
        # get url
        if not self.url_obj:
            self.url_obj = self.url_q.safe_get()
        else:
            try:
                self.logger.debug("Downloading: {}".format(self.url_obj.url))
                # make request
                with requests.Session() as s:
                    try:
                        resp = s.get(
                            self.url_obj.url,
                            allow_redirects=True,
                            timeout=self.DEFAULT_POLLING_TIMEOUT * 15,
                        )
                        self.logger.debug(
                            "Response for: {} is {}".format(
                                self.url_obj.url, resp.status_code
                            )
                        )
                    except requests.ReadTimeout:

                        self.logger.warn(
                            "Download timeout - Retrying URL: {}".format(
                                self.url_obj.url
                            )
                        )
                        time.sleep(self.DEFAULT_POLLING_TIMEOUT)
                        self.request.mark_as_requested(
                            status_code=408,
                            requested_url=self.url_obj.url,
                            final_url=None,
                        )
                        return

                # if successfull store file
                if resp.status_code == 200:
                    self.logger.debug("Storing file for {}".format(self.url_obj.url))
                    generated_uuid = uuid.uuid4()
                    open(
                        self.PATH + str(generated_uuid) + self.url_obj.file_ending, "wb"
                    ).write(resp.content)

                self.logger.debug(
                    "Storing crawling result for: {}".format(self.url_obj.url)
                )
                # store crawling result in crawling table
                self.request.mark_as_requested(
                    status_code=resp.status_code,
                    requested_url=self.url_obj.url,
                    final_url=resp.url,
                    content_uuid=str(generated_uuid),
                    url_id=self.url_obj.url_id,
                )
                self.url.mark_as_crawled(self.url_obj)
                self.logger.info("Downloaded: {}".format(self.url_obj.url))

                self.url_obj = None
            except TimeoutError:
                pass
