import datetime
from datetime import timezone

import psycopg2
from psycopg2 import sql

from .tables import Table


class SessionDay(Table):
    """
    Models the days the parliament met

    The SessionDay table is used to store all possible days a plenary session could have occured. We check for a session by crawling for the existence of a matching protocol and store the hit (or lack of) in the hit-column.
    A job deriving all possible URLs from the date can then sort by the hit-property and create them.

    Attributes:
        dates : date
            the date of a possible session
        hit : boolean
            did HEAD-ing a generated result not return a 404

    """

    schema = "public"
    table_name = "session_days"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            dates date NOT NULL,
                            CONSTRAINT session_days_pkey PRIMARY KEY (id),
                            CONSTRAINT date_unique UNIQUE (dates)
                          );"""

    def get_unchecked_days(
        self,
        limit=10,
        offset=datetime.timedelta(days=30),
        start_date=datetime.date(1994, 1, 1),
        sessiondayrulename="session_day",
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

        query = """ (SELECT days
                    FROM(
                        /*all dates between two dates*/
                        SELECT days::date
                        FROM   generate_series(timestamp %s
                                        , timestamp %s
                                        , interval  '1 day')AS days
                        ) s
                    LEFT JOIN (
                        /*URLs generated by SessionDayCheckers Rules*/
                        SELECT *
                        FROM session_days
                        LEFT JOIN urls on session_days.id = urls.date_id
                        WHERE rule_id = (
                            /*Rule used to generate SessionDayChecker URLs*/
                            SELECT id
                            FROM rules
                            WHERE rulename = %s)
                        ) stored
                    /*LEFT JOIN generated with already stored dates */
                    ON s.days = stored.dates
                    /*LEFT JOIN results in NULL where no data is available in stored*/
                    WHERE stored.dates is NULL
                    ORDER by s.days desc
                    LIMIT %s)
                    /*combine results with already created dates which weren't crawled successfull*/

                    UNION ALL

                    (/*return dates which have no successfull sessio_day requests associated */
                    SELECT session_days.dates
                    FROM urls
                    LEFT JOIN session_days on session_days.id=urls.date_id
                    LEFT JOIN requests on requests.url_id=urls.id
                    LEFT JOIN rules on urls.rule_id = rules.id
                    WHERE rules.id = (SELECT id FROM rules WHERE rulename =%s) and session_days.dates not in (
                        /*get all dates with successfull sesion_day requests*/
                        SELECT session_days.dates
                        FROM urls
                        LEFT JOIN session_days on session_days.id=urls.date_id
                        LEFT JOIN requests on requests.url_id=urls.id
                        LEFT JOIN rules on urls.rule_id = rules.id
                        WHERE rules.id = (SELECT id FROM rules WHERE rulename =%s) and status_code in (200,404))
                    LIMIT %s)
                    LIMIT %s


                    """

        date = datetime.date.today() - offset

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    start_date,
                    date,
                    sessiondayrulename,
                    # the limit here is set to 9 to leave one space free to recrawl unsuccessfully crawled dates
                    limit - 1,
                    sessiondayrulename,
                    sessiondayrulename,
                    limit,
                    limit,
                ],
            )
            data = [row[0] for row in db.cur.fetchall()]
            return data

    def insert_date(self, date):
        query = """ INSERT INTO session_days(dates)
                    VALUES(%s)
                    ON CONFLICT (dates)
                    DO
                        UPDATE SET dates=%s
                    RETURNING id;
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [date, date],
            )
            value = db.cur.fetchone()[0]
        return value

    def get_date(self, id):
        query = """ SELECT id, dates
                    FROM session_days
                    WHERE id = %s"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [id],
            )
            value = db.cur.fetchone()
        return value
