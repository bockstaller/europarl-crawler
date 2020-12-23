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
                            CONSTRAINT rules_pkey PRIMARY KEY (id),
                            CONSTRAINT name_unique UNIQUE (rulename)
                          );"""

    def register_rule(self, rulename):
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
        rulename = str(rulename)

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [rulename, rulename],
            )
            value = db.cur.fetchone()[0]
        return value

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
        query_name = """ SELECT id, rulename
                    FROM   public.rules
                    WHERE  rulename = %s ;"""

        query_id = """ SELECT id, rulename
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
