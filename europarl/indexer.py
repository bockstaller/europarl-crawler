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
from elasticsearch import Elasticsearch, helpers

from europarl import rules
from europarl.crawler import create_table_structure, init_rules, read_config
from europarl.db import DBInterface, Documents, Rules, SessionDay, URLs, tables
from europarl.elasticinterface import create_index, get_current_index
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.workers import Indexer


def main():
    config = read_config()

    with MainContext(config) as main_ctx:

        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        create_table_structure(main_ctx.config)

        es = Elasticsearch(config["Indexer"].get("ESConnection"))
        indexname = config["Indexer"].get("ESIndexname")

        index = get_current_index(es, indexname)
        if not index:
            index = create_index(es, indexname)

        main_ctx.Proc(
            name="Indexer",
            worker_class=Indexer,
            config=config["Indexer"],
        )

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


if __name__ == "__main__":
    main()
