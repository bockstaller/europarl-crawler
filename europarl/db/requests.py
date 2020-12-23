from collections import Counter
from datetime import datetime, timezone

from psycopg2 import sql

from .tables import Table


class Request(Table):

    schema = "public"
    table_name = "requests"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            url_id integer,
                            requested_at timestamp with time zone,
                            status_code integer,
                            content_uuid uuid,
                            requested_url varchar(2000),
                            final_url varchar(2000),
                            CONSTRAINT requests_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_url FOREIGN KEY (url_id)
                                REFERENCES public.urls (id)
                                    ON DELETE NO ACTION
                          );"""
    index_definition = """  CREATE INDEX requested_at_index
                            ON public.requests USING btree
                            (requested_at DESC NULLS LAST)"""

    def get_request_log(self, id):
        query = """ SELECT status_code, requested_url, final_url, requested_at, content_uuid, url_id
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
        status_code,
        requested_url,
        final_url,
        requested_at=datetime.now(tz=timezone.utc),
        content_uuid=None,
        url_id=None,
    ):
        query = """ INSERT INTO public.requests(status_code, requested_url, final_url, requested_at, content_uuid, url_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    status_code,
                    requested_url,
                    final_url,
                    requested_at,
                    content_uuid,
                    url_id,
                ],
            )
            value = db.cur.fetchone()[0]
        return value

    def get_status_code_summary(self, start_time, end_time):
        query = """ SELECT status_code
                    FROM   public.requests
                    WHERE  requested_at BETWEEN SYMMETRIC %s AND %s ;"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [start_time, end_time],
            )
            rows = db.cur.fetchall()

        counter = Counter()
        counter.update([row[0] for row in rows])

        return counter