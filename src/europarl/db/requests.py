from datetime import datetime, timezone

from psycopg2 import sql

from .tables import Table


class Request(Table):

    schema = "public"
    table_name = "requests"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            url_id integer,
                            requested_at time with time zone,
                            status_code integer,
                            content uuid,
                            requested_url varchar(2000),
                            final_url varchar(2000),
                            CONSTRAINT requests_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_url FOREIGN KEY (url_id)
                                REFERENCES public.urls (id)
                                    ON DELETE NO ACTION
                          );"""

    def mark_as_requested(
        self,
        status_code,
        requested_url,
        final_url,
        requested_at=datetime.now(tz=timezone.utc),
        content_uuid=None,
        url_id=None,
    ):
        query = """ INSERT INTO requests(status_code, requested_url, final_url, requested_at, content, url_id)
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
            return db.cur.fetchone()
