import json
from datetime import date, datetime, timezone

from psycopg2.extras import execute_batch

from .tables import Table


class Documents(Table):
    """
    Database table which stores documents and all of its associated metadata and provides methods to interact with this data

    Attributes:
        filepath (str):
            the path where the file is stored
        filename (unique uuid):
            uuid used as the filename
        data (jsonb):
            extracted data and metadata for this document
        downloaded_at (datetime.datetime):
            timestamp when the document was originaly downloaded
        enequeued (boolean):
            true if the document is queued up for postprocessing
        indexed (boolean):
            true if the document is stored in elasticsearch
        unindex (boolean):
            marker to unindex this document

    """

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
        """
        Stores a document in the table

        Args:
            filepath (str): path to the place where the document is stored on the system
            filename (uuid): uuid of the document
            downloaded_at (datetime.datetime, optional): Timestamp when the document was downloaded. Defaults to ```datetime.now(tz=timezone.utc)```.

        Returns:
            int: id of the database entry
        """

        query = """ INSERT INTO documents(filepath, filename, downloaded_at)
                    VALUES ( %s, %s, %s)
                    RETURNING id
                """

        if downloaded_at is None:
            downloaded_at = datetime.now(tz=timezone.utc)

        with self.db.cursor() as db:
            db.cur.execute(
                query,
                [filepath, filename, downloaded_at],
            )
            result = db.cur.fetchone()[0]

        return result

    def get_unprocessed_documents(self, limit=10):
        """
        Get downloaded documents that aren't processed and aren't already queued up for postprocessing

        Args:
            limit (int, optional): Amount of documents that should be retrieved. Defaults to 10.

        Returns:
            list of dicts: dict containing the rule id and name for the document and the document id and filepath
        """
        query = """ SELECT rules.id, rules.rulename, documents.id, documents.filepath
                    FROM documents
                    LEFT JOIN requests ON requests.document_id=documents.id
                    LEFT JOIN urls on requests.url_id=urls.id
                    LEFT JOIN rules on urls.rule_id=rules.id
                    WHERE rules.rulename is not NULL and rules.active=True and documents.enqueued =False
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
        """
        Marks a document as queued up.

        Could be integrated into get_uprocessed_documents by converting it into update-returning SQL call.

        Args:
            document_id (int): id of the document entry
        """
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
        """
        Removes all enqueued-locking by setting the field to false where no data is associated with the document.
        """
        query = """ UPDATE documents
                    SET enqueued = False
                    WHERE documents.data is Null
                """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
            )

    def get_data(self, document_id):
        """
        Returns the data extracted from a document.

        Args:
            document_id (int): document id

        Returns:
            dict: dictionary containing the document id and the data stored under the 'data' key
        """
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
        """
        Sets data for a document

        Args:
            document_id (int): document id
            data (dict): dictionary of all data

        """
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
        """
        Collects the metadata associated with document that is available in the database

        Args:
            document_id (int): document id

        Returns:
            dict: dict containing all metadata fields as separate keys
        """
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
        """
        Gets a list of document ids and the data associated with it for indexing

        Args:
            limit (int, optional): Amount of datasets that should be retrieved. Defaults to 100.

        Returns:
            list of id and dict tuples: pairings of id and data
        """
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
        """
        Mark a document as indexed

        Args:
            ids (int): list of ids
        """
        query = """ UPDATE documents
                    SET indexed = true
                    WHERE documents.id =%s;
                """

        with self.db.cursor() as db:
            execute_batch(db.cur, query, ids)

        return

    def reset_all_postprocessing(self):
        """
        Drop all postprocessing resetting results and mark them for unindexing.
        """
        query = """ UPDATE documents
                    SET enqueued=False, data=NULL, unindex=d.indexed
                    WHERE true;
                    """

        with self.db.cursor() as db:
            db.cur.execute(
                query,
            )

        return

    def reset_postprocessing_by_rule(self, rule_id):
        """
        Drop all postprocessing results for documents which are related to the passed rule and mark them for unindexing.

        Args:
            rule_id (int): Rule id to select postprocessing results to remove
        """
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
        """
        Get all documents which are marked for unindexing

        Returns:
            list of ids: List of ids of documents marked for unindexing
        """

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
        """
        Mark documents as successfully unindexed

        Args:
            ids (list of ints): List of document ids to update
        """
        query = """ UPDATE documents as d
                    SET unindex = False, indexed=False
                    WHERE d.id =%s;
                """

        with self.db.cursor() as db:
            db.cur.executemany(query, ids)

        return
