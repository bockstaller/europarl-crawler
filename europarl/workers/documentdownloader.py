import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests
from fake_useragent import UserAgent

from europarl.db import DBInterface, Documents, Request, URLs
from europarl.mptools import QueueProcWorker


class DocumentDownloader(QueueProcWorker):

    DATAPATH = "../data/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_args(self, args):
        (
            self.work_q,
            self.url_q,
        ) = args

    def startup(self):
        """"""
        super().startup()

        self.DATAPATH = self.config["Path"]
        self.REQUEST_TIMEOUT = float(self.config["RequestTimeoutFactor"]) * float(
            self.config["StopWaitSecs"]
        )

        self.ua = UserAgent()

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.request = Request(self.db)
        self.url = URLs(self.db)
        self.docs = Documents(self.db)

        self.logger.info("{} started".format(self.name))

        self.url_id, self.url_str = None, None

        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Dnt": "1",
            "Referer": "https://www.google.com",
        }

    def shutdown(self):
        """"""
        super().shutdown()

    def main_func(self, token):
        # get url
        if not self.url_id:
            self.logger.debug("Getting new URL")
            self.url_id = self.url_q.safe_get()

            if self.url_id is None:
                self.work_q.safe_put(token)
                time.sleep(self.DEFAULT_POLLING_TIMEOUT)
                self.logger.debug("No work - returning")
                return

            url = self.url.get_url(id=self.url_id)
            self.url_str = url["url"]
            self.filetype = url["filetype"]

        try:

            self.logger.debug("Downloading: {}".format(self.url_str))

            with requests.Session() as ses:
                ses.headers = self.headers
                ses.headers["User-Agent"] = self.ua.random
                resp = ses.get(
                    self.url_str,
                    allow_redirects=True,
                    timeout=self.REQUEST_TIMEOUT,
                )
            self.logger.debug(
                "Response for: {} is {}".format(self.url_str, resp.status_code)
            )

            self.request.mark_as_requested(
                url_id=self.url_id,
                status_code=resp.status_code,
                redirected_url=resp.url,
            )
        except requests.ReadTimeout as e:

            self.logger.warn("Timeout for url: {}".format(self.url_str))
            self.logger.warn("Exception Message: {}".format(e))

            self.request.mark_as_requested(
                url_id=self.url_id, status_code=408, redirected_url=self.url_str
            )
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
            return

        except requests.RequestException as e:
            self.logger.warn("Request exception for url: {}".format(self.url_str))
            self.logger.warn("Exception Message: {}".format(e))
            self.request.mark_as_requested(
                url_id=self.url_id, status_code=460, redirected_url=self.url_str
            )
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
            return

        doc_id = None
        # if successfull store file
        if resp.status_code == 200:
            self.logger.debug("Storing file for {}".format(self.url_str))
            file_uuid = str(uuid.uuid4())
            filename = file_uuid + self.filetype
            abspath = os.path.abspath(self.DATAPATH)
            filepath = abspath + "/" + filename

            open(filepath, "wb").write(resp.content)

            doc_id = self.docs.register_document(filepath=filepath, filename=file_uuid)
        else:
            self.request.mark_as_requested(
                self.url_id,
                status_code=resp.status_code,
                redirected_url=resp.url,
                document_id=doc_id,
            )

        self.logger.info("Crawled: {}".format(self.url_str))

        self.url_id, self.url_str, self.filetype = None, None, None
