import configparser
import datetime
import json
import logging
import multiprocessing
import os
import random
import socket
import sys
import time
from datetime import date
from queue import Full

import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from europarl import rules
from europarl.crawler import create_table_structure, init_rules, read_config
from europarl.db import DBInterface, Documents, Rules, SessionDay, URLs, tables
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.workers import (
    DateUrlGenerator,
    DocumentDownloader,
    PostProcessingScheduler,
    PostProcessingWorker,
    SessionDayChecker,
    TokenBucketWorker,
)


def main():
    config = read_config()

    with Context(config) as main_ctx:

        create_table_structure(main_ctx.config)
        create_index(config)

        init_rules(main_ctx.config)

        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        document_q = main_ctx.MPQueue(30)

        for instance_id in range(
            int(config["PostProcessingWorker"].get("Instances", 1))
        ):
            main_ctx.Proc(
                document_q,
                config["Elasticsearch"],
                name="PostProcessingWorker_{}".format(instance_id),
                worker_class=PostProcessingWorker,
                config=config["PostProcessingWorker"],
            )

        main_ctx.Proc(
            document_q,
            name="PostProcessingScheduler",
            worker_class=PostProcessingScheduler,
            config=config["PostProcessingScheduler"],
        )

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


def create_index(config):
    es = Elasticsearch(config["Elasticsearch"].get("Connection"))
    indexname = config["Elasticsearch"].get("Indexname")
    if not es.indices.exists(indexname):
        with open("./europarl_index.json", "r") as file:
            index_definition = json.load(file)

        es.indices.create(index=indexname, body=index_definition)

    es.close()


class Context(MainContext):
    def stop_procs(self):
        super(Context, self).stop_procs()
        temp_db = DBInterface(config=self.config["General"])

        docs = Documents(temp_db)
        self.logger.info("Resetting scheduled documents")
        docs.reset_enqueued()


if __name__ == "__main__":
    main()
