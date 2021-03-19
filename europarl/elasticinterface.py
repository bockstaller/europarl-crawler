import json
import logging

from elasticsearch import Elasticsearch, helpers


def get_actions(documents, indexname, op_type):
    """
    Generator for yielding action objects that do not require object data, which can be used by elasticsearchs bulk methods.

    Args:
        documents (list): list of document data tuples from the database
        indexname (str): index on which the action should be used
        op_type (str): operation name

    Yields:
        dict: elasticsearch bulk action dictionary
    """
    for row in documents:
        value = {
            "_id": row[0],
            "_index": indexname,
            "_op_type": op_type,
        }
        yield (value)


def get_actions_data(documents, indexname, op_type):
    """
    Generator for yielding action objects that do require object data, which can be used by elasticsearchs bulk methods.

    Args:
        documents (list): list of document data tuples from the database
        indexname (str): index on which the action should be used
        op_type (str): operation name

    Yields:
        dict: elasticsearch bulk action dictionary
    """
    for row in documents:

        value = {
            "_id": row[0],
            "_index": indexname,
            "_op_type": op_type,
            **row[1],
        }
        yield (value)


def manage_documents(es, docs, action, indexname, documents, function, silent=False):
    """
    Interface function to interact with an elasticsearch index.
    Gets the current active index, initiates the desired operations in bulk,
    and returns a list of successfull operations.

    Args:
        es: elasticsearch instance
        action (str): desired operation
        indexname (str): configured indexname
        documents (list): list of documents
        function (generator): generator function used to generate the actions
        silent (bool, optional): Should errors be ignored. Defaults to False.

    Returns:
        list(int): list of successfull document ids
    """
    index = get_current_index(es, indexname)

    bulk_result = helpers.streaming_bulk(
        es,
        function(documents, index, action),
        raise_on_error=not (silent),
        chunk_size=100,
        max_retries=10,
        initial_backoff=2,
        max_backoff=60,
    )

    bulk_results = [result[0] for result in list(bulk_result)]

    successfull = list(
        zip(
            [document[0] for document in documents],
            [result for result in bulk_results],
        )
    )

    successfull_ids = [(item[0],) for item in successfull if item[1] is True]

    return successfull_ids


def index_documents(es, docs, action, indexname, documents, silent=False):
    """
    Wrapper for manage documents, preselecting ``get_actions(...)``
    """
    return manage_documents(es, docs, action, indexname, documents, get_actions, silent)


def index_documents_data(es, docs, action, indexname, documents, silent=False):
    """
    Wrapper for manage documents, preselecting ``get_actions_data(...)``
    """
    return manage_documents(
        es, docs, action, indexname, documents, get_actions_data, silent
    )


def create_index(es, indexname, mapping=None):
    """
    Create a index based upon the configured base indexname. It will increment an appendend 5 digit number to version the different index instances.

    Args:
        es : elasticsearch instance
        indexname (str): configured base indexname
        mapping (dict, optional): Dict with the index mapping. Defaults to the content of europarl/europarl_index.json.

    Returns:
        str: complete index name
    """
    current_index = get_current_index(es, indexname)
    if not current_index:
        index = indexname + "-" + "00000"
    else:
        next_index_number = int(current_index.split("-")[1]) + 1
        index = indexname + "-" + f"{next_index_number:05d}"

    if not es.indices.exists(index):
        if not mapping:
            with open("europarl/europarl_index.json", "r") as file:
                mapping = json.load(file)

        es.indices.create(index=index, body=mapping)

    return index


def get_current_index(es, indexname):
    """
    Return the current complete index name base upon the configured base index name.

    Args:
        es: elasticsearch instance
        indexname (str): base index name

    Returns:
        str: complete index name
    """
    indices = es.indices.resolve_index(indexname + "*")["indices"]
    index_names = [index["name"] for index in indices]

    if len(indices) > 0:
        index_numbers = [int(index.split("-")[1]) for index in index_names]
        current_index = max(index_numbers)
        return indexname + "-" + f"{current_index:05d}"
    else:
        return None
