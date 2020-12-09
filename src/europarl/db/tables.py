import datetime
from abc import ABC
from contextlib import contextmanager
from types import SimpleNamespace

import psycopg2
import pytz
from psycopg2 import sql


class Table(ABC):
    """
    Abstract baseclass implementing common table functions


    """

    def __init__(self, DBInterface):
        """Creates a new instance of the table class

        Args:
            DBInterface (DBInterface): DBInterface instance to execute the commands
        """
        self.db = DBInterface

    def create_table(self):
        """Creates the table in the database by executing it's table definition

        Returns:
            boolean: True if the table was created successfully
        """

        with self.db.cursor() as db:
            db.cur.execute(
                sql.SQL(self.table_definition).format(
                    schema=sql.Identifier(self.schema),
                    table=sql.Identifier(self.table_name),
                )
            )

    def table_exists(self):
        """Checks if the table exists in the database

        Returns:
            boolean: True if the table exists in the database
        """

        with self.db.cursor() as db:

            db.cur.execute(
                sql.SQL(
                    """ SELECT EXISTS
                        (
                            SELECT 1
                            FROM pg_tables
                            WHERE schemaname = {schema}
                            AND tablename = {table}
                        )
                    """
                ).format(
                    schema=sql.Literal(self.schema),
                    table=sql.Literal(self.table_name),
                )
            )
            return db.cur.fetchone()[0]


class SessionDay(Table):
    """
    Models the days the parliament met

    The SessionDay table is used to store all possible days a plenary session could have occured. We check for a session by crawling for the existence of a matching protocol and store the hit (or lack of) in the hit-column.
    A job deriving all possible URLs from the date can then sort by the hit-property and create them. The creation status is tracked in urls_created and urls_created_date.

    Attributes:
        dates : date
            the date of a possible session
        hit : boolean
            did HEAD-ing a generated result not return a 404
        status_code : integer
            returned status-code from crwaling the response
        checked: boolean not null defaults false
            was this url checked
        checked_at: timestamp utc
            when was this url last checked
        urls_created : boolean
            True if a url generator has already derived urls from the date
        urls_created_ts: datetime
            When did a url generator derive urls from the date

    """

    schema = "public"
    table_name = "session_days"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            dates date NOT NULL,
                            hit boolean NOT NULL DEFAULT false,
                            status_code integer,
                            checked boolean NOT NULL DEFAULT false,
                            checked_at time with time zone,
                            urls_created boolean NOT NULL DEFAULT false,
                            urls_created_at time with time zone,
                            CONSTRAINT session_days_pkey PRIMARY KEY (id),
                            CONSTRAINT date_unique UNIQUE (dates)
                          );"""

    def get_unchecked_days(
        self,
        limit=10,
        offset=datetime.timedelta(days=30),
        start_date=datetime.date(1994, 1, 1),
    ):
        """
        Returns all dates not stored in the table which match the offset and start_date criteria.
        The checked time span is all days between the start_date and today-offset.

        Args:
            limit (int): Amount of days the function should return at most. Defaults to 10
            offset (datetime.timedelta, optional): Amount off days, starting from today, that will be ignored. Defaults to 30.
            start_date (datetime.date, optional): [description]. Defaults to datetime.date(1994, 1, 1).

        Returns:
            [datetime.date]: List of dates with a maximum number of limit entries
        """

        query = """ SELECT 	s.days
                    FROM(
                        SELECT days::date
                        FROM   generate_series(timestamp %s
                                        , timestamp %s
                                        , interval  '1 day')AS days
                        ) s
                    FULL OUTER JOIN session_days on session_days.dates = s.days::date
                    WHERE session_days.checked is Null or session_days.checked = False
                    ORDER by s.days desc
                    LIMIT %s;"""

        date = datetime.date.today() - offset

        with self.db.cursor() as db:
            db.cur.execute(query, [start_date, date, limit])
            data = [row[0] for row in db.cur.fetchall()]
            return data

    def update_day(self, date, status_code, hit=False, checked=False):
        query = """ INSERT INTO session_days(dates, hit, status_code, checked, checked_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (dates)
                    DO
                        UPDATE SET hit = %s, status_code = %s, checked = %s, checked_at = %s
                        WHERE session_days.dates = %s
                    RETURNING id
                """

        checked = checked
        checked_at = datetime.datetime.now(pytz.utc)

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    date,
                    hit,
                    status_code,
                    checked,
                    checked_at,
                    hit,
                    status_code,
                    checked,
                    checked_at,
                    date,
                ],
            )
            return db.cur.fetchone()


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
                            id integer NOT NULL,
                            rule VARCHAR(100) NOT NULL,
                            url TEXT NOT NULL,
                            found boolean NOT NULL,
                            created time with time zone NOT NULL,
                            enqueued boolean NOT NULL,
                            enqueued_at time with time zone,
                            enqueued_times integer NOT NULL,
                            crawled boolean NOT NULL,
                            crawled_at time with time zone,
                            failed boolean NOT NULL,
                            file_path TEXT,
                            recrawl boolean NOT NULL,
                            recrawl_after time with time zone,
                            PRIMARY KEY(id)
                          );"""
