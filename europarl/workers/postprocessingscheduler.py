import time
from datetime import datetime, timedelta, timezone
from queue import Full

from europarl.db import DBInterface, Documents, Rules, SessionDay
from europarl.mptools import ProcWorker


class PostProcessingScheduler(ProcWorker):
    def init_args(self, args):
        (self.document_q,) = args

    def startup(self):
        super().startup()

        self.PREFETCH_LIMIT = int(self.config["PrefetchLimit"])

        self.db = DBInterface(config=self.config)
        self.db.connection_name = self.name

        self.documents = Documents(self.db)
        self.todo_documents = []
        self.current_document = None
        self.logger.info("{} started".format(self.name))

    def shutdown(self):
        super().shutdown()

    def main_func(self):
        """
        This function requests a number of unpostprocessed documents from the database and enqueues them into the postprocessing queue.
        """

        if len(self.todo_documents) == 0:
            self.logger.debug("Requesting new documents")
            self.todo_documents = self.documents.get_unprocessed_documents(
                limit=self.PREFETCH_LIMIT
            )
            if len(self.todo_documents) == 0:
                time.sleep(self.DEFAULT_POLLING_TIMEOUT * 10)
                self.logger.debug("No new documents recieved")
            else:
                self.logger.debug(
                    "Recieved {} new documents".format(len(self.todo_documents))
                )

            return

        if self.current_document is None:
            self.current_document = self.todo_documents.pop()
            self.documents.mark_as_enqueued(self.current_document["document"]["id"])

        try:
            self.logger.debug(
                "Queueing up Document with id: {}".format(
                    self.current_document["document"]["id"]
                )
            )
            self.document_q.put(
                self.current_document, timeout=self.DEFAULT_POLLING_TIMEOUT
            )
            self.logger.info(
                "Queued up document with id: {}".format(
                    self.current_document["document"]["id"]
                )
            )
            self.current_document = None
        except Full:
            self.logger.debug("Queue full - retrying")
