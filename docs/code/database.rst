
Database
--------

DB-Interface
^^^^^^^^^^^^

.. autoclass:: europarl.db.interface
    :members:


Tables
^^^^^^

Tables
""""""

.. autoclass:: europarl.db.tables.Table
    :members:


SessionDay
""""""""""

The SessionDay table is used to store all possible days a plenary session could have occured. We check for a session by crawling for the existence of a matching protocol and store the hit (or lack of) in the hit-column.
A job deriving all possible URLs from the date can then sort by the hit-property and create them. The creation status is tracked in urls_created and urls_created_date.

.. autoclass:: europarl.db.tables.SessionDay
    :members:


URLs
""""

The URLs table stores all crawling metadata to crawled, scheduled to be crawled  and found urls.
This table is mainly populated by url generators which create urls to crawl by for example basing them on parliament session dates. Crawlers are then responsible for storing the crawling metadata for each url and can additionally append found urls.

.. autoclass:: europarl.db.tables.URLs
    :members:




