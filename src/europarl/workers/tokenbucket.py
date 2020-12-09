from queue import Full

from europarl.mptools import TimerProcWorker


class TokenBucketWorker(TimerProcWorker):
    """
    Creates tokens for the crawlers to use and enques them in the bucket queue which must be passed as an arg-

    """

    INTERVAL_SECS = 0.2
    DEFAULT_POLLING_TIMEOUT = 0.1

    token_nr = 0

    def init_args(self, args):
        (self.token_bucket_q,) = args

    def main_func(self):
        """
        The token-string carries no meaning and is only intended for debugging purposes.
        The continous creating, waiting and discarding loop in case of a full token_bucket_q keeps the process responsive to shutdown signals which are handled in the base class TimerProcWorker.
        """

        token = "{}:{:04d}".format(self.name, self.token_nr)
        self.logger.debug("Created token: {}".format(token))

        self.logger.debug("Enqueing token: {}".format(token))

        try:
            self.token_bucket_q.put(token, timeout=self.DEFAULT_POLLING_TIMEOUT)
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
