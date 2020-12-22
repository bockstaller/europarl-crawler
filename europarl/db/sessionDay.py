import datetime
from datetime import timezone

import psycopg2
from psycopg2 import sql

from .tables import Table


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
        generated_url: varchar(2000)
            generated url that was checked
        final_url: varchar(2000)
            url the websever directed the crawler to
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
                            generated_url varchar(2000),
                            final_url varchar(2000),
                            checked boolean NOT NULL DEFAULT false,
                            checked_at time with time zone,
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

    def update_day(
        self, date, status_code, generated_url, final_url, hit=False, checked=False
    ):
        query = """ INSERT INTO session_days(dates, hit, status_code, checked, checked_at, generated_url, final_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (dates)
                    DO
                        UPDATE SET hit = %s, status_code = %s, checked = %s, checked_at = %s, generated_url = %s, final_url = %s
                        WHERE session_days.dates = %s
                    RETURNING id
                """

        checked = checked
        checked_at = datetime.datetime.now(tz=timezone.utc)

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    date,
                    hit,
                    status_code,
                    checked,
                    checked_at,
                    generated_url,
                    final_url,
                    hit,
                    status_code,
                    checked,
                    checked_at,
                    generated_url,
                    final_url,
                    date,
                ],
            )
            return db.cur.fetchone()
