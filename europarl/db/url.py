from datetime import datetime, timezone

from psycopg2 import sql

from .tables import Table


class URL:
    """
    URL object for passing around via queues
    """

    # TODO drop date, url and file ending elements and use only the _id fields in all places where URL is used

    date_id = None
    rule_id = None
    url_id = None
    date = None
    url = None
    file_ending = None

    def __init__(self, date_id, rule_id, url, date=None, url_id=None, file_ending=None):
        """
        Initializes a URL object

        Args:
            date_id (int): Database id of the date from which this url was derived
            rule_id (int): Database id of the rule from which this url was derived
            url (string): String of the url
            date (datetime.date, optional): Defaults to None.
            url_id (integer, optional): Defaults to None.
            file_ending (str, optional): Defaults to None.
        """
        self.date_id = date_id
        self.rule_id = rule_id
        self.url_id = url_id
        self.url = url
        self.file_ending = file_ending


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
                            crawled_at time with time zone,
                            CONSTRAINT urls_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_date FOREIGN KEY (date_id)
                                REFERENCES public.session_days (id)
                                    ON DELETE CASCADE,
                            CONSTRAINT fk_rule FOREIGN KEY (rule_id)
                                REFERENCES public.rules (id)
                                    ON DELETE CASCADE
                          );"""
    index_definition = """  CREATE EXTENSION IF NOT EXISTS pgcrypto;

                            CREATE UNIQUE INDEX "unique_url"
                            ON {schema}.{table}
                            USING btree (digest(url, 'sha512'::text));

                            CREATE INDEX fk_date_id
                         ON public.urls USING btree
                            (date_id ASC NULLS LAST)
"""

    def dates_with_less_derived_urls_than(self, amount_rules, limit):
        """
        Returns dates which do not have the necessary amount of urls generated. This is for example the case if a new rule is added and now rules where derived up unitl now.

        Args:
            amount_rules (int): current amount of rules
            limit (int): amount of dates that should be returned

        Returns:
            [dict]: List of dicts with the keys date_id (primary key of the date) and date (datetime.date object)
        """
        # TODO compute amount of rules on the fly and change whereever it is used

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
            result = [{"date_id": x[0], "date": x[1]} for x in db.cur.fetchall()]
        return result

    def mark_as_generated(self, derived_urls):
        """
        Stores a url as generated

        Args:
            derived_urls ([URL]): list of URL-objects that should be stored

        Returns:
            [URL]: list of updated URL-objects now containing updated url objects
        """

        query = """ INSERT INTO urls(date_id, rule_id, url, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (digest(url, 'sha512'::text))
                    DO
                        UPDATE SET date_id=%s, rule_id=%s, created_at=%s
                        WHERE urls.url = %s
                    RETURNING id
                """
        updated_derived_urls = []

        for url in derived_urls:
            with self.db.cursor() as db:
                db.cur.execute(
                    query,
                    [
                        url.date_id,
                        url.rule_id,
                        url.url,
                        datetime.now(tz=timezone.utc),
                        url.date_id,
                        url.rule_id,
                        datetime.now(tz=timezone.utc),
                        url.url,
                    ],
                )
                result = db.cur.fetchone()
                if result:
                    url.url_id = result[0]
                    updated_derived_urls.append(url)

        return updated_derived_urls

    def mark_as_crawled(self, url):
        """
        Marks a url as already crawled

        Args:
            url (URL): URL-object to update in the database

        Returns:
            int: id of updated url element
        """
        query = """
                    UPDATE urls
                    SET crawled = 'true', crawled_at = %s
                    WHERE urls.id = %s AND urls.url = %s
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [datetime.now(tz=timezone.utc), url.url_id, url.url],
            )
            result = db.cur.fetchone()
            if result:
                return result[0]
            return None

    def drop_uncrawled_urls(self):
        """
        Removes all uncrawled urls from the database
        """
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
