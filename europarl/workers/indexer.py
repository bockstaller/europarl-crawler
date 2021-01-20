import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from multiprocessing.queues import Full

import requests
from elasticsearch import Elasticsearch, helpers

from europarl import rules
from europarl.db import DBInterface, Documents, Request, URLs
from europarl.mptools import ProcWorker


class Indexer(ProcWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def startup(self):
        """"""
        super().startup()

        self.index = self.config["ESIndexname"]
        self.es = Elasticsearch(self.config["ESConnection"])

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name
        self.docs = Documents(self.db)

        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        """"""
        super().shutdown()

    def main_func(self):

        documents = self.docs.get_unindexed_data()

        bulk_result = helpers.streaming_bulk(
            self.es,
            self.get_actions(documents, self.index, "create"),
            raise_on_error=False,
            chunk_size=100,
        )

        successfull = [result[0] for result in list(bulk_result)]

        indexed = list(
            zip(
                [document[0] for document in documents],
                [result for result in successfull],
            )
        )

        self.docs.set_indexed(indexed)

        self.logger.info(
            "Indexed {} documents successfully out of {} documents in the batch".format(
                sum(successfull), len(successfull)
            )
        )

    def get_actions(self, documents, indexname, op_type):
        for row in documents:

            value = {
                "_id": row[0],
                "_index": indexname,
                "_op_type": op_type,
                **row[1],
            }
            yield (value)
