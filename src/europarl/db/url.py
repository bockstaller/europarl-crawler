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
                            url text NOT NULL,
                            CONSTRAINT urls_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_date FOREIGN KEY (date_id)
                                REFERENCES public.session_days (id)
                                    ON DELETE CASCADE
                          );"""

    def dates_with_less_derived_urls_than(self, amount_rules, limit):
        query = """SELECT session_days.id ,session_days.dates
                    FROM session_days
                    FULL OUTER JOIN urls ON session_days.id = urls.date_id
                    GROUP BY session_days.id
                    HAVING COUNT(urls.id) < %s
                    ORDER BY session_days.id
                    LIMIT %s"""
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [amount_rules, limit],
            )
            return db.cur.fetchone()
