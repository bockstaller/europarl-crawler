from datetime import datetime, timezone

from .tables import Table


class Documents(Table):
    """"""

    schema = "public"
    table_name = "documents"
    table_definition = """CREATE TABLE IF NOT EXISTS {schema}.{table}(
                            id SERIAL,
                            filepath VARCHAR(2000),
                            filename uuid UNIQUE,
                            downloaded_at timestamp with time zone,
                            CONSTRAINT documents_pkey PRIMARY KEY (id)
                          );"""

    def register_document(
        self,
        filepath,
        filename,
        downloaded_at=datetime.now(tz=timezone.utc),
    ):
        query = """ INSERT INTO documents(filepath, filename, downloaded_at)
                    VALUES ( %s, %s, %s)
                    RETURNING id
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [filepath, filename, downloaded_at],
            )
            result = db.cur.fetchone()[0]

        return result
