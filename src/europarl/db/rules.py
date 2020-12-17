from .tables import Table


class Rules(Table):

    schema = "public"
    table_name = "rules"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            rulename VARCHAR(100),
                            CONSTRAINT rules_pkey PRIMARY KEY (id),
                            CONSTRAINT name_unique UNIQUE (rulename)
                          );"""

    def register_rule(self, name):
        query = """ INSERT INTO rules(rulename)
                    VALUES (%s)
                    ON CONFLICT (rulename)
                    DO
                        UPDATE SET rulename=%s
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [name, name],
            )
            return db.cur.fetchone()[0]
