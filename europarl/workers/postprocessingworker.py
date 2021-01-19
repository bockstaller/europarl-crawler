import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests
from elasticsearch import Elasticsearch

from europarl import rules
from europarl.db import DBInterface, Documents, Request, URLs
from europarl.mptools import QueueProcWorker


class PostProcessingWorker(QueueProcWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_args(self, args):
        (
            self.work_q,
            self.es_config,
        ) = args

    def startup(self):
        """"""
        super().startup()

        self.es = Elasticsearch(self.es_config["Connection"])
        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.docs = Documents(self.db)

        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        """"""
        super().shutdown()

    def main_func(self, document):

        try:
            metadata = self.docs.get_metadata(document["document"]["id"])

            document_data = None
            document_data = rules.RULES[document["rule"]["name"]].extract_data(
                document["document"]["filepath"]
            )

            data = {**metadata, **document_data}

            ret = self.es.index(
                index=self.es_config["Indexname"],
                id=document["document"]["id"],
                body=data,
            )
            print(ret)

            self.docs.set_data(document["document"]["id"], data)
            self.logger.info("Processed document {}".format(document["document"]["id"]))

        except NotImplementedError:
            self.logger.info(
                "Document {} not processed. No postprocessing rule implemented".format(
                    document["document"]["id"]
                )
            )
