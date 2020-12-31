import configparser
import datetime
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

from europarl import rules
from europarl.db import DBInterface, Rules, SessionDay, URLs, tables
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
    SessionDayChecker,
    TokenBucketWorker,
)


def main():
    config = read_config()

    with Context(config) as main_ctx:

        create_table_structure(main_ctx.config)
        init_rules(main_ctx.config)

        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(100)
        url_q = main_ctx.MPQueue(10)

        main_ctx.Proc(
            token_bucket_q,
            name="SessionDayChecker",
            worker_class=SessionDayChecker,
            config=config["SessionDayChecker"],
        )

        for instance_id in range(int(config["Downloader"].get("Instances", 1))):
            main_ctx.Proc(
                token_bucket_q,
                url_q,
                name="Downloader_{}".format(instance_id),
                worker_class=DocumentDownloader,
                config=config["Downloader"],
            )

        main_ctx.Proc(
            url_q,
            name="DateUrlGenerator",
            worker_class=DateUrlGenerator,
            config=config["DateUrlGenerator"],
        )
        main_ctx.Proc(
            token_bucket_q,
            name="TokenGenerator",
            worker_class=TokenBucketWorker,
            config=config["TokenBucketWorker"],
        )

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


def read_config():
    config = configparser.ConfigParser()
    config.read("../settings.ini")
    return config


def create_table_structure(config):

    temp_db = DBInterface(config=config["General"])

    for table in tables:
        table_inst = table(temp_db)
        if not table_inst.table_exists():
            table_inst.create_table()
        del table_inst

    temp_db.close()


def init_rules(config):
    temp_db = DBInterface(config=config["General"])
    r = Rules(temp_db)
    r.register_rules(rules.RULES)


class Context(MainContext):
    def stop_procs(self):
        super(Context, self).stop_procs()
        temp_db = DBInterface(config=self.config["General"])
        urls = URLs(temp_db)
        # drop uncrawled urls last to prevent race conditions
        self.logger.info("Dropping uncrawled urls")
        urls.drop_uncrawled_urls()


if __name__ == "__main__":
    main()
