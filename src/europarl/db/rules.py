from .tables import Table


class Rules(Table):

    schema = "public"
    table_name = "rules"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            name VARCHAR(100),
                            CONSTRAINT rules_pkey PRIMARY KEY (id),
                            CONSTRAINT name_unique UNIQUE (name)
                          );"""

    def register_rule(self, name):
        query = """ INSERT INTO rules(name)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING

                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [name],
            )
            return db.cur.fetchone()
