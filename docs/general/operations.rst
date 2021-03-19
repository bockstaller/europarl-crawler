Command line interface
======================

The running application can be controlled via a CLI which uses the same configuration file to interact with the database and elasticsearch. "--help" can be used in addition to the listed commands to get an explanation of what the commands do.

Rules
-----

``eurocli rules``

Lists all currently registred rules, their id's, language, and fileformat in a

``eurocli rules -r 1 --activate/--deactivate``

Enables/Disables the rule with the id passed with the -r parameter

Crawler
-------

``eurocli crawler start``

Starts the crawler job

Postprocessing
--------------

``eurocli postprocessing start``

Starts the postprocessing jobs

``eurocli postprocessing reset -r 1``

Clears the postprocessing resets for the passed rule and unindexes all postprocessing results from Elasticsearch. The indexed bit is only reset for documents where this unindexing was successful.

``eurocli postprocessing reset -r 1 -f``

Clears the postprocessing resets for the passed rule and unindexes all postprocessing results from Elasticsearch. The indexed bit is reset for all documents associated with this rule.

Indexing
--------

``eurocli indexing start``

Starts the indexing job

``eurocli indexing unindex``

Retries the unindexing operation from ``eurocli postprocessing reset -r 1``

``eurocli indexing reindex /path/to/new/mapping.json``

Creates a new index based upon the passed mapping, transfers all old entries to the new index and reroutes the running indexing operation to the new index.