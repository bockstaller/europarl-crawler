import logging
import multiprocessing
import random
import socket
import sys
import time
from queue import Full

from europarl.mptools import (
    EventMessage,
    MainContext,
    ProcWorker,
    QueueProcWorker,
    TimerProcWorker,
    default_signal_handler,
    init_signals,
)

DEFAULT_POLLING_TIMEOUT = 0.1
MAX_SLEEP_SECS = 0.02


class TokenBucketWorker(TimerProcWorker):
    INTERVAL_SECS = 0.01

    token_nr = 0

    def init_args(self, args):
        (self.token_bucket_q,) = args

    def main_func(self):
        """
        Creates tokens for the crawlers.
        The token-string carries no meaning and is only intended for debugging purposes.
        The continous creating, waiting and discarding loop in case of a full token_bucket_q keeps the process responsive to shutdown signals which are handled in the base calass TimerProcWorker.
        """

        token = "{}:{:04d}".format(self.name, self.token_nr)
        self.logger.debug("Created token: {}".format(token))

        self.logger.debug("Enqueing token: {}".format(token))

        try:
            self.token_bucket_q.put(token, timeout=DEFAULT_POLLING_TIMEOUT)
            self.logger.info("Enqueued token: {}".format(token))
        except Full:
            self.logger.debug("Queue full. - Discarding token: {}".format(token))
            return

        if self.token_nr >= 1000:
            self.token_nr = 0
            self.logger.debug("Token number overflow. Reseted to 0")
        else:
            self.token_nr += 1
            self.logger.debug("Incremented token number to {}".format(self.token_nr))


def request_handler(event, reply_q, main_ctx):
    main_ctx.logger.log(logging.DEBUG, f"request_handler - '{event.msg}'")


def main():
    with MainContext() as main_ctx:
        init_signals(
            main_ctx.shutdown_event, default_signal_handler, default_signal_handler
        )

        token_bucket_q = main_ctx.MPQueue(200)

        main_ctx.Proc("TOKEN_GEN0", TokenBucketWorker, token_bucket_q)

        while not main_ctx.shutdown_event.is_set():
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue


if __name__ == "__main__":
    main()
