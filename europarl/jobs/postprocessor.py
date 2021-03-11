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

from europarl import configuration
from europarl.db import (
    DBInterface,
    Documents,
    Rules,
    SessionDay,
    URLs,
    create_table_structure,
    tables,
)
from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)
from europarl.rules import rule
from europarl.workers import PostProcessingScheduler, PostProcessingWorker


def main():
    config = configuration.read()

    with Context(config) as main_ctx:

        create_table_structure(main_ctx.config)

        db = DBInterface(config=main_ctx.config["DEFAULT"])
        Rules(db).register_rules(rule.rule_registry.all)
        db.close()

        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        document_q = main_ctx.MPQueue(30)

        for instance_id in range(
            int(config["PostProcessingWorker"].get("Instances", 1))
        ):
            main_ctx.Proc(
                document_q,
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


class Context(MainContext):
    def stop_procs(self):
        super(Context, self).stop_procs()
        temp_db = DBInterface(config=self.config["General"])

        docs = Documents(temp_db)
        self.logger.info("Resetting scheduled documents")
        docs.reset_enqueued()


if __name__ == "__main__":
    main()
