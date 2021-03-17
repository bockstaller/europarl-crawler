from collections import Counter
from datetime import datetime, timezone

from psycopg2 import sql

from .tables import Table


class Request(Table):
    """
    Database table to log the requests the application makes

    Attributes:
        id (int): id of the document
        url_id (int): foreign key to the url table
        document_id (int): foreign key to the document table
        requested_at (datetime.datetime): timestamp of the request
        status_code (integer): HTTP response code of the request
        redirected_url (string): the URL the webserver redirected to

    """

    schema = "public"
    table_name = "requests"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            url_id integer,
                            document_id integer,
                            requested_at timestamp with time zone,
                            status_code integer,
                            redirected_url varchar(2000),
                            CONSTRAINT requests_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_url FOREIGN KEY (url_id)
                                REFERENCES public.urls (id)
                                    ON DELETE SET NULL,
                            CONSTRAINT fk_document FOREIGN KEY (document_id)
                                REFERENCES public.documents (id)
                                    ON DELETE SET NULL
                          );"""
    index_definition = """  CREATE INDEX requested_at_index
                            ON public.requests USING btree
                            (requested_at DESC NULLS LAST)"""

    def get_request_log(self, id):
        """
        Return data associated to the request id

        Args:
            id (int): request id

        Returns:
            tuple: tuple containing the request id, related url id, related document id, request timestamp, status code and redirected-to url
        """
        query = """ SELECT id, url_id, document_id, requested_at, status_code, redirected_url
                    FROM public.requests
                    WHERE id = %s
        """
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [id],
            )
            value = db.cur.fetchone()
        return value

    def mark_as_requested(
        self,
        url_id,
        status_code,
        redirected_url,
        document_id=None,
        requested_at=None,
    ):
        """
        Logs a request in the database

        Args:
            url_id (int): reference to the url used for the request
            status_code (int): http status code
            redirected_url (string): redirected-to url
            document_id (integer, optional): Reference to the downloaded document. Defaults to None.
            requested_at (datetime.datetime, optional): Timestamp of the request. Defaults to ```datetime.now(tz=timezone.utc)```.

        Returns:
            [type]: [description]
        """
        if requested_at is None:
            requested_at = datetime.now(tz=timezone.utc)

        query = """ INSERT INTO requests(url_id, document_id, requested_at, status_code, redirected_url)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [url_id, document_id, requested_at, status_code, redirected_url],
            )
            value = db.cur.fetchone()[0]
        return value

    def get_status_code_summary(self, start_time, end_time):
        """
        Returns a counter which counts the occurences of the individuall status codes

        Args:
            start_time (datetime.datetime): start of the time interval to count status codes
            end_time (datetime.datetime): end of the time interval to count the status codes

        Returns:
            collections.Counter: Counter object with all the status code occurences summed up
        """
        query = """ SELECT status_code
                    FROM   public.requests
                    WHERE  requested_at >= %s AND requested_at <= %s;"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [start_time, end_time],
            )

            rows = db.cur.fetchall()

        counter = Counter()
        counter.update([row[0] for row in rows])

        return counter
