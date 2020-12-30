from europarl import rules
from europarl.db.sessionDay import SessionDay
from europarl.db.url import URLs

from .tables import Table


class Rules(Table):
    """
    Stores the rules for refernce

    Attributes:
        id (int): id and primary key of the rule
        rulename(str): unique name of the rule

    """

    schema = "public"
    table_name = "rules"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            rulename VARCHAR(100),
                            filetype VARCHAR(6),
                            language VARCHAR(6),
                            active BOOLEAN default FALSE,
                            CONSTRAINT rules_pkey PRIMARY KEY (id),
                            CONSTRAINT name_unique UNIQUE (rulename)
                          );"""

    def register_rules(self, rulenames):
        """
        Registers a rule by it's unique name

        Args:
            rulename (str): rulename, must be unique

        Returns:
            int: id of the registered rule
        """
        query = """ INSERT INTO rules(rulename, filetype, language)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (rulename)
                    DO
                        UPDATE SET rulename=%s, filetype=%s, language=%s
                    RETURNING id
                """
        ids = []

        for rulename in rulenames:
            func = getattr(rules, rulename)
            language = getattr(func, "language", None)
            filetype = getattr(func, "format", None)

            with self.db.cursor() as db:
                db.cur.execute(
                    query,
                    [rulename, filetype, language, rulename, filetype, language],
                )
                ids.append(db.cur.fetchone()[0])
        return ids

    def get_rule(self, id=None, rulename=None):
        """
        Gets a rule out of the database either by a passed rulename or by a passed id. One parameter must be provided.

        Args:
            id (int, optional): id of the rule to get out of the database. Defaults to None.
            rulename (str, optional): name of the rule to get out of the database.. Defaults to None.

        Raises:
            AttributeError: Gets raised if neither an id or a name is provided

        Returns:
            (int, str): tuple consisting out of the id and the name of the rule
        """
        query_name = """ SELECT id, rulename, active
                    FROM   public.rules
                    WHERE  rulename = %s ;"""

        query_id = """ SELECT id, rulename, active
                    FROM   public.rules
                    WHERE  id = %s ;"""

        if id:
            query = query_id
            parameter = id
        elif rulename:
            query = query_name
            parameter = str(rulename)
        else:
            raise AttributeError

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [parameter],
            )
            value = db.cur.fetchone()
        return value

    # TODO: Test
    def update_rule_state(self, id, active=False):
        query = """ UPDATE rules
                    SET active=%s
                    WHERE id = %s
                    RETURNING id
                """
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [active, id],
            )
            value = db.cur.fetchone()
        return value

    # TODO: Test
    def apply_rules(self, date_id):
        query = """ SELECT id, rulename
                    FROM rules
                    WHERE active = True;
                """

        with self.db.cursor() as db:
            db.cur.execute(query)
            active_rules = db.cur.fetchall()

        s = SessionDay(self.db)
        date = s.get_date(id=date_id)[1]

        u = URLs(self.db)

        url_ids = []
        for rule_id, rulename in active_rules:
            url = rules.RULES[rulename](date)
            url_ids.append(u.save_url(date_id=date_id, rule_id=rule_id, url=url))

        return url_ids

    # TODO: Test
    def apply_rule(self, rule_id, date_id):
        rule_id, rulename, active = self.get_rule(id=rule_id)

        s = SessionDay(self.db)
        date = s.get_date(id=date_id)[1]

        url = rules.RULES[rulename](date)

        u = URLs(self.db)
        url_id = u.save_url(date_id=date_id, rule_id=rule_id, url=url)

        return url_id, url
