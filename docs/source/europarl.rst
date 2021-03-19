europarl package
================

Subpackages
-----------

.. toctree::
   :maxdepth: 4

   europarl.db
   europarl.rules
   europarl.workers
   europarl.jobs
   europarl.mptools

Submodules
----------

europarl.configuration module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module is responsible for loading the configuration files.

.. automodule:: europarl.configuration
   :members:
   :undoc-members:
   :show-inheritance:

europarl.elasticinterface module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module contains the functions used to interact with elasticsearch.

.. automodule:: europarl.elasticinterface
   :members:
   :undoc-members:
   :show-inheritance:

europarl.eurocli module
^^^^^^^^^^^^^^^^^^^^^^^

This module uses the click package to implement the command line interface used for managing the crawler.

.. autofunction:: europarl.eurocli.main

.. autofunction:: europarl.eurocli.cli

.. autofunction:: europarl.eurocli.crawler_start

.. autofunction:: europarl.eurocli.rules_function

.. autofunction:: europarl.eurocli.postprocessing_start

.. autofunction:: europarl.eurocli.postprocessing_reset

.. autofunction:: europarl.eurocli.indexing_start

.. autofunction:: europarl.eurocli.indexing_unindex

.. autofunction:: europarl.eurocli.indexing_reindex

