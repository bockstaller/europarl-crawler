from datetime import datetime, timezone

from psycopg2 import sql

from .tables import Table


class URLs(Table):
    """
    Stores information about URLs

    The URLs table stores all crawling metadata to crawled, scheduled to be crawled  and found urls.
    This table is mainly populated by url generators which create urls to crawl by for example basing them on parliament session dates. Crawlers are then responsible for storing the crawling metadata for each url and can additionally append found urls.

    Attributes:

        rule : VARCHAR(100)
            name of the rule used to generate the URL
        url : TEXT
            the generated URL
        found : boolean
             True if a crawler found this URL in a document
        enqueued : boolean
            True if the URLGenerator has enqueued the URL to be crawled, is set to False on startup
        crawled : boolean
            has this URL been crawled
        crawled_at : datetime
            when has this URL been crawled
        file_path : TEXT
            where is the downloaded document stored
        recrawl : boolean
            should this url be recrawled
        recrawl_after : datetime
            the document will be recrawled sometime after this timestamp

    """

    schema = "public"
    table_name = "urls"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            date_id integer,
                            rule_id integer,
                            url VARCHAR(2000) NOT NULL,
                            created_at time with time zone,
                            crawled boolean NOT NULL DEFAULT false,
                            CONSTRAINT urls_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_date FOREIGN KEY (date_id)
                                REFERENCES public.session_days (id)
                                    ON DELETE CASCADE,
                            CONSTRAINT fk_rule FOREIGN KEY (rule_id)
                                REFERENCES public.rules (id)
                                    ON DELETE CASCADE,
                            UNIQUE(url)
                          );"""

    def dates_with_less_derived_urls_than(self, amount_rules, limit):
        query = """SELECT session_days.id ,session_days.dates
                    FROM session_days
                    FULL OUTER JOIN urls ON session_days.id = urls.date_id
                    WHERE session_days.hit = true
                    GROUP BY session_days.id
                    HAVING COUNT(urls.id) < %s
                    ORDER BY session_days.id
                    LIMIT %s"""
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [amount_rules, limit],
            )
            return [{"date_id": x[0], "date": x[1]} for x in db.cur.fetchall()]

    def mark_as_generated(self, derived_urls):
        query = """ INSERT INTO urls(date_id, rule_id, url, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url)
                    DO
                        UPDATE SET date_id=%s, rule_id=%s, created_at=%s
                        WHERE urls.url = %s
                    RETURNING id
                """

        for url in derived_urls:
            with self.db.cursor() as db:
                db.cur.execute(
                    query,
                    [
                        url["date_id"],
                        url["rule_id"],
                        url["url"],
                        datetime.now(tz=timezone.utc),
                        url["date_id"],
                        url["rule_id"],
                        datetime.now(tz=timezone.utc),
                        url["url"],
                    ],
                )
                url["url_id"] = db.cur.fetchone()

    def drop_uncrawled_urls(self):
        query = """ DELETE FROM {schema}.{table}
                    WHERE crawled = false;
                """

        with self.db.cursor() as db:
            db.cur.execute(
                sql.SQL(query).format(
                    schema=sql.Identifier(self.schema),
                    table=sql.Identifier(self.table_name),
                )
            )
