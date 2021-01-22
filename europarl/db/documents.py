import json
from datetime import date, datetime, timezone

from psycopg2.extras import execute_batch

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
                            indexed boolean DEFAULT False,
                            unindex boolean DEFAULT False,
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
                    WHERE rules.rulename is not NULL and documents.enqueued =False
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

        def default_converter(o):
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, date):
                return o.isoformat()
            else:
                str(o)

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [json.dumps(data, default=default_converter), document_id],
            )

    def get_metadata(self, document_id):
        query = """SET TIMEZONE='UTC';
        SELECT documents.filepath, documents.downloaded_at, requests.redirected_url, session_days.dates, rules.rulename, rules.filetype, rules.language
        FROM documents
        LEFT JOIN requests ON requests.document_id = documents.id
        LEFT JOIN urls on urls.id=requests.url_id
        LEFT JOIN session_days on urls.date_id = session_days.id
        LEFT JOIN rules on urls.rule_id = rules.id
        WHERE documents.id = %s;
        """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [document_id],
            )
            data = db.cur.fetchone()

        keys = [
            "filepath",
            "downloaded_at",
            "url",
            "session_date",
            "rulename",
            "filetype",
            "language",
        ]

        result = dict(zip(keys, data))
        return result

    def get_unindexed_data(self, limit=100):
        query = """ SELECT id, data
                    FROM documents
                    WHERE data is not NULL
                    AND indexed = false
                    LIMIT %s"""

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [
                    limit,
                ],
            )

            res = db.cur.fetchall()

        return res

    def set_indexed(self, ids):
        query = """ UPDATE documents
                    SET indexed = true
                    WHERE documents.id =%s;
                """

        with self.db.cursor() as db:
            execute_batch(db.cur, query, ids)

        return

    def reset_all_postprocessing(self):
        query = """ UPDATE documents
                    SET enqueued=False, data=NULL
                    WHERE true;
                    """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
            )

        return

    def reset_postprocessing_by_rule(self, rule_id):
        query = """ UPDATE documents as d
                    SET enqueued=False, data=NULL, unindex=d.indexed
                    FROM requests as r
                    LEFT JOIN urls ON urls.id = r.url_id
                    WHERE urls.rule_id = %s AND r.document_id=d.id
                    """

        with self.db.cursor() as db:
            db.cur.execute(query, [rule_id])

        return

    def get_documents_to_unidex(self):
        query = """ SELECT id
                    FROM documents
                    WHERE unindex = true
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
            )

            res = db.cur.fetchall()

        return res

    def reset_unindex(self, ids):
        query = """ UPDATE documents as d
                    SET unindex = False, indexed=False
                    WHERE d.id =%s;
                """

        with self.db.cursor() as db:
            db.cur.executemany(query, ids)

        return
