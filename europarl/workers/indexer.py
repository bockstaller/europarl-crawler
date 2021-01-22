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
from europarl.elasticinterface import (
    get_actions,
    get_actions_data,
    get_current_index,
    index_documents,
    index_documents_data,
)
from europarl.mptools import ProcWorker


class Indexer(ProcWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def startup(self):
        """"""
        super().startup()

        self.es = Elasticsearch(self.config["ESConnection"])
        self.indexname = self.config["ESIndexname"]

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name
        self.docs = Documents(self.db)

        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        """"""
        super().shutdown()

    def main_func(self):
        try:
            documents = self.docs.get_unindexed_data(limit=10)

            if len(documents) > 0:

                deleted_ids = index_documents(
                    self.es, self.docs, "delete", self.indexname, documents, silent=True
                )

                if len(deleted_ids) > 0:
                    self.logger.warn(
                        "Deleted {} documents successfully out of {} documents in the batch".format(
                            len(deleted_ids), len(documents)
                        )
                    )

                successfull_ids = index_documents_data(
                    self.es, self.docs, "index", self.indexname, documents, silent=True
                )

                self.docs.set_indexed(successfull_ids)

                self.logger.info(
                    "Indexed {} documents successfully out of {} documents in the batch".format(
                        len(successfull_ids), len(documents)
                    )
                )

        except Exception as e:
            self.logger.error(e)

        finally:
            time.sleep(self.DEFAULT_POLLING_TIMEOUT)
