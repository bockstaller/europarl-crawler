import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests

from europarl import rules
from europarl.db import DBInterface, Documents, Request, URLs
from europarl.mptools import QueueProcWorker


class PostProcessingWorker(QueueProcWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def startup(self):
        """"""
        super().startup()

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.docs = Documents(self.db)

        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        """"""
        super().shutdown()

    def main_func(self, document):

        data = None
        try:
            data = rules.RULES[document["rule"]["name"]].extract_data(
                document["document"]["filepath"]
            )
            self.docs.set_data(document["document"]["id"], data)
            self.logger.info("Processed document {}".format(document["document"]["id"]))
        except NotImplementedError:
            self.logger.info(
                "Document {} not processed. No postprocessing rule implemented".format(
                    document["document"]["id"]
                )
            )
