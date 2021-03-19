europarl.rules package
======================

Every document variant consisting out of document subtype, filetype, and language has an individual rule set governing the creation of the URL to the document and the data extraction methods applied to it.

These rules are collected and stored in the database during the startup of the application. They can be individually toggled to control if they should be applied upon session dates and downloaded documents.


Comparsion between the text extraction quality from a .html vs. a .pdf file depending on the document type over time
Currently, there are 18 different document rules implemented allowing for the download of daily agendas, agendas, protocols, voting overviews, named voting, and word protocols in English and German in HTML and PDF formats.

These rules have two data extraction methods implemented, filesize and file content. Filesize gets the filesize for the downloaded document while file content extracts the text from the document depending on the file format. The plot on the right shows the quality of the PDF text extraction method using the text from the HTML file as a baseline.

europarl.rules.rule module
--------------------------

.. automodule:: europarl.rules.rule
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.agenda module
----------------------------

.. automodule:: europarl.rules.agenda
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.dailyAgenda module
---------------------------------

.. automodule:: europarl.rules.dailyAgenda
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.extraction module
--------------------------------

.. automodule:: europarl.rules.extraction
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.protocol module
------------------------------

.. automodule:: europarl.rules.protocol
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.votingNamed module
---------------------------------

.. automodule:: europarl.rules.votingNamed
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.votingOverview module
------------------------------------

.. automodule:: europarl.rules.votingOverview
   :members:
   :undoc-members:
   :show-inheritance:

europarl.rules.wordprotocol module
----------------------------------

.. automodule:: europarl.rules.wordprotocol
   :members:
   :undoc-members:
   :show-inheritance:

