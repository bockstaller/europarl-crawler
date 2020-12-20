from datetime import datetime, timedelta, timezone
from queue import Full

from europarl.db import Request
from europarl.mptools import TimerProcWorker


class TokenBucketWorker(TimerProcWorker):
    """
    Creates tokens for the crawlers to use and enques them in the bucket queue which must be passed as an arg-

    """

    MIN_INTERVAL_SECS = 0.2
    INTERVAL_SECS = MIN_INTERVAL_SECS
    DEFAULT_POLLING_TIMEOUT = 0.1
    THROTTLING_INTERVAL = 1

    token_nr = 0
    last_check = None
    next_check = None

    def init_args(self, args):
        (self.token_bucket_q, self.db) = args
        self.db.connection_name = self.db.connection_name + " - TokenBucket"
        self.request = Request(self.db)

    def throttle(self):
        self.logger.debug("Emptying Token Bucket")
        self.token_bucket_q.drain()

        if self.INTERVAL_SECS < self.MIN_INTERVAL_SECS * 100000:
            self.INTERVAL_SECS = self.INTERVAL_SECS * 2
            self.logger.info(
                "Throttling resulted in a sleeping interval of {} seconds".format(
                    self.INTERVAL_SECS
                )
            )

    def unthrottle(self):
        if self.INTERVAL_SECS > self.MIN_INTERVAL_SECS:
            self.INTERVAL_SECS = self.INTERVAL_SECS / 2
            self.logger.info(
                "Unthrottling resulted in a sleeping interval of {} seconds".format(
                    self.INTERVAL_SECS
                )
            )

    def apply_throttling(self, status_codes):
        """
        Matches the passed status_codes against the rquirements for throttling the token generation

        Args:
            status_codes (list(int)): List of status_codes as integers
        """
        if any(item in [408, 429] for item in status_codes):
            self.logger.info("Requesting throttling because of server rate limiting.")
            self.throttle()
            return
        if any(item in list(range(500, 599)) for item in status_codes):
            self.logger.info("Requesting throttling because of server errors.")
            self.throttle()
            return
        self.logger.info("Requesting unthrottling")
        self.unthrottle()

    def check_throttling(self, now):
        """
        Checks if it is time to check for throttling due to error requests.

        If necessary gets the status codes, updates the timestamps for the next checks and passes the status_codes array to the apply_throttling function

        Args:
            now (datetime(tz)): current timestamp
        """
        self.logger.debug("Check if a throttling check is necessary.")
        if now > self.next_check:
            self.logger.debug("Checking status codes")
            status_codes = self.request.get_status_code_summary(
                self.last_check, now
            ).keys()

            self.logger.debug("Setting checking timerange for next iteration")
            self.last_check = now
            self.next_check = now + timedelta(seconds=self.THROTTLING_INTERVAL)
            self.apply_throttling(status_codes)

    def startup(self):
        """
        Initializes the last and next check timestamps
        """
        super().startup()
        self.last_check = datetime.now(tz=timezone.utc)
        self.next_check = self.last_check + timedelta(seconds=self.THROTTLING_INTERVAL)

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
            self.check_throttling(datetime.now(tz=timezone.utc))
        except Full:
            self.logger.debug("Queue full. - Discarding token: {}".format(token))
            return

        if self.token_nr >= 1000:
            self.token_nr = 0
            self.logger.debug("Token number overflow. Reseted to 0")
        else:
            self.token_nr += 1
            self.logger.debug("Incremented token number to {}".format(self.token_nr))
