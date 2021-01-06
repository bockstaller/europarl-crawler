import json
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
                            enqueued boolean DEFAULT False,
                            data jsonb,
                            downloaded_at timestamp with time zone,
                            CONSTRAINT documents_pkey PRIMARY KEY (id)
                          );"""

    def register_document(
        self,
        filepath,
        filename,
        downloaded_at=None,
    ):
        if downloaded_at is None:
            downloaded_at = datetime.now(tz=timezone.utc)
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

    def get_unprocessed_documents(self, limit=10):
        query = """ SELECT rules.id, rules.rulename, documents.id, documents.filepath
                    FROM documents
                    LEFT JOIN requests ON requests.document_id=documents.id
                    LEFT JOIN urls on requests.url_id=urls.id
                    LEFT JOIN rules on urls.rule_id=rules.id
                    WHERE documents.data is NULL AND rules.rulename is not NULL and documents.enqueued =False
                    ORDER by requests.requested_at ASC
                    LIMIT %s
                """
        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [limit],
            )
            documents = db.cur.fetchall()

        result = []
        for item in documents:
            result.append(
                {
                    "rule": {"id": item[0], "name": item[1]},
                    "document": {"id": item[2], "filepath": item[3]},
                }
            )

        return result

    def mark_as_enqueued(self, document_id):
        query = """ UPDATE documents
                    SET enqueued = True
                    WHERE documents.id = %s
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [document_id],
            )

    def reset_enqueued(self):
        query = """ UPDATE documents
                    SET enqueued = False
                    WHERE documents.data is Null
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
            )

    def get_data(self, document_id):
        query = """ SELECT documents.id, documents.data
                    FROM documents
                    WHERE documents.id = %s"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [document_id],
            )
            document = db.cur.fetchone()

        return {"id": document[0], "data": json.loads(document[1])}

    def set_data(self, document_id, data):
        query = """ UPDATE documents
                    SET data = %s
                    WHERE documents.id=%s
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [json.dumps(data), document_id],
            )
