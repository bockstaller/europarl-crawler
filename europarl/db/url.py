from datetime import datetime, timezone

from psycopg2 import sql

from europarl import rules

from .tables import Table


class URLs(Table):
    """
    Stores information about URLs

    The URLs table stores all crawling metadata to crawled, scheduled to be crawled  and found urls.
    This table is mainly populated by url generators which create urls to crawl by for example basing them on parliament session dates. Crawlers are then responsible for storing the crawling metadata for each url and can additionally append found urls.

    Attributes:
        date_ud : Integer
            reference to the date used to generate the url
        rule_id : Integer
            reference to the rule used to generate the url
        url : TEXT
            the generated URL
        created_at : timestamp with timezone
            Timestamp when url was created


    """

    schema = "public"
    table_name = "urls"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            date_id integer,
                            rule_id integer,
                            url VARCHAR(2000) NOT NULL,
                            created_at time with time zone,
                            CONSTRAINT urls_pkey PRIMARY KEY (id),
                            CONSTRAINT fk_date FOREIGN KEY (date_id)
                                REFERENCES public.session_days (id)
                                    ON DELETE SET NULL,
                            CONSTRAINT fk_rule FOREIGN KEY (rule_id)
                                REFERENCES public.rules (id)
                                    ON DELETE SET NULL,
                            UNIQUE (rule_id, url)

                          );"""
    index_definition = """  CREATE EXTENSION IF NOT EXISTS pgcrypto;

                            CREATE INDEX fk_date_id
                            ON public.urls USING btree
                            (date_id ASC NULLS LAST)
                            """

    def save_url(self, date_id, rule_id, url, created_at=None):
        """
        Stores a url as generated

        Args:
            date_id (int): reference to the date used to generate the url
            rule_id (int): reference to the rule used to generate the url
            url (str): generated url
            created_at (datetime with timezone): time of url generation

        Returns:
            int: id of url
        """
        if created_at is None:
            created_at = datetime.now(tz=timezone.utc)

        query = """ INSERT INTO urls(date_id, rule_id, url, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (rule_id, url)
                    DO
                        UPDATE SET created_at=%s
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    date_id,
                    rule_id,
                    url,
                    created_at,
                    created_at,
                ],
            )
            result = db.cur.fetchone()[0]

        return result

    def get_todo_rule_and_date_combos(self, limit):
        """
        Returns a tuple of date and rule combinations that should exist but don't, based upon the active rules, session_dates and already created rules

        Args:
            limit (int): amount of dates that should be returned

        Returns:
            (int, datetime.date, int, str): tuple consisting out of session_days id, session_days date, rule id and rule name
        """

        query = """ SELECT  session_days.id,
                            session_days.dates,
                            rules.id,
                            rules.rulename
                    FROM session_days
                    /*Cross join rules and session_days to get all possible combinations */
                    CROSS JOIN rules
                    LEFT JOIN urls
                        ON urls.rule_id=rules.id
                        AND urls.date_id=session_days.id
                    /*From all rule & day-combinations only the active ones without derived URLs are from interest*/
                    WHERE active = true AND urls.id IS NULL
                    /*which had successfull crawling results*/
                    AND session_days.dates IN (
                        /*Get all dates with successfull session_day crawling results*/
                        SELECT session_days.dates FROM session_days
                        INNER JOIN urls ON urls.date_id = session_days.id
                        INNER JOIN requests ON requests.url_id = urls.id
                        INNER JOIN rules ON urls.rule_id=rules.id
                        WHERE rules.rulename = %s AND requests.status_code = 200
                    )
                    ORDER BY dates DESC
                    LIMIT %s;"""
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [rules.protocol.SessionDayRule.name, limit],
            )
            result = db.cur.fetchall()

        keys = ["date_id", "date", "rule_id", "rulename"]
        result_dict = [dict(zip(keys, values)) for values in result]
        return result_dict

    def drop_uncrawled_urls(self):
        """
        Removes all uncrawled urls from the database
        """
        query = """
                DELETE
                FROM urls
                WHERE urls.id IN (
                    SELECT urls.id
                    FROM urls
                    LEFT JOIN requests
                    ON requests.url_id=urls.id
                    WHERE requests.url_id is NULL
                );
                """

        with self.db.cursor() as db:
            db.cur.execute(query)

    def get_url(self, id=None):
        # TODO: testing
        query = """ SELECT  urls.id, urls.url, rules.filetype
                    FROM    public.urls
                    JOIN    rules
                    ON rules.id = urls.rule_id
                    WHERE  urls.id = %s ;"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [id],
            )
            value = db.cur.fetchone()

            ret = {"id": value[0], "url": value[1], "filetype": value[2]}
        return ret
