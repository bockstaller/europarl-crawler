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
        query = """ INSERT INTO rules(rulename)
                    VALUES (%s)
                    ON CONFLICT (rulename)
                    DO
                        UPDATE SET rulename=%s
                    RETURNING id
                """
        ids = []

        for rulename in rulenames:
            with self.db.cursor() as db:
                db.cur.execute(
                    query,
                    [rulename, rulename],
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

    def apply_rule(self, rulename, date_id):
        rule_id, rulename, active = self.get_rule(rulename=rulename)
        s = SessionDay(self.db)
        date = s.get_date(id=date_id)[1]

        u = URLs(self.db)

        url = rules.RULES[rulename](date)
        url_id = u.save_url(date_id=date_id, rule_id=rule_id, url=url)

        return url_id, url
