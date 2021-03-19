
Extending the system
====================

The current system can be extended mainly by adding/extending rules or adding new workers. The process of how to setup the development environment is outlined in the README.md file of the repository.

These are the main extension points for this project.

Adding or extending existing rules
----------------------------------
A rule has the task to generate crawlable URLs and extract as much data as possible from a retrieved document.

The module europarl.rules implement an abstract base class Rule, which defines the minimal interface necessary.
A rule-class has to provide a unique name, a language, and file format as attributes while implementing a URL(date) and extract_data(file path) class method.
They have to be decorated with the @rule_registry decorator from the same module, to be registered during application startup. All rules are identified by their name and are not active by default.

The function URL(date) must return a valid URL as a string when called with a DateTime.date parameter. The function extract_data(file path) must return a dictionary containing all extracted data when called. Dictionary keys and values will be used directly in Elasticsearch. Examples implementing the two methods are provided in the europarl.rules module.
These properties are tested by tests in tests.rules.test_rule.

Adding new attributes to the extract_data dictionary will make changes to the Elasticsearch mapping necessary. Update the europarl_index.json as needed and use the cli's reindex command to transfer existing data to a new and updated index.

Adding new workers
------------------
New workers can be used to inject new data into the processing pipeline or add additional processing steps.

Workers are implemented using the ProcWorker, TimerProcWorker, and QueueProcWorker base classes of the mptools module.
The ProcWorker class implements a continuously running main loop with setup and teardown functions. This main loop calls a main_func-function which has to be overwritten to implement the needed business logic.
The TimerProcWorker calls its main_func-function only if the specified interval has been exceeded. The QueueProcWorker consumes the elements of a multiprocessing queue and calls its main function while passing this item. Multiple workers can add or retrieve items from a queue object as they are wrapped multiprocessing.queue objects.

Workers are implemented as separate subprocesses and communicate with the instantiating jobs via signals and queues. Therefore every worker has to poll the respective signal to know if it should terminate. This is handled by the three worker base classes but requires relatively fast exiting main_func-functions to poll the exit-signal and finish cleanup during the time specified in the StopWaitSecs configuration option.
Long-running tasks should be split up into smaller tasks and return the main function before resuming in the next iteration.
A worker might store data regarding the process in the database, for example for locking database entries as queued up for processing. This should be cleaned up in the teardown function of the worker and preferably in the jobs teardown method as well. This prevents locking entries permanently if the application gets interrupted.

These workers are then integrated into a job by instantiating a new Process with a descriptive name, the class of the worker, and a configuration option. Additional attributes like an input or output queue can be passed as well.
An imaginary worker, which produces URLs by picking a random string every 10 seconds, would be implemented as a TimerProcWorker. It would enqueue its URL into the passed URL-queue, for the downloader worker to process.

Future Work
===========

Cataloging document versions
----------------------------

The crawler is currently set up to crawl an URL only once, because the DateUrlGenerater-Worker is only queueing up freshly generated URLs for the DocumentDownloader to process. This could be changed by adding an additional worker responsible for repeadetly requeuing URLs associated with recent dates. These repeated requests could track changes of a document over time, for which the basic support in the postgres data modell is already there. As a URL can be related to multiple requests, which can be related to a downloaded file.
The indexer worker would need additional changes to support indexing multiple versions of a document.

Crawling published texts
------------------------

Cataloging multiple document versions would allow for proper support of the tabled and accepted texts document types
The challenge is due to the fact that these documents follow only a partial date dependent naming scheme and change over time. With the complication that the changes in these documents are meaningfull and interessting in contrast to most editorial changes to a protocol.
Currently only a very simplistic rule for these documents could be implementd. One where the first january every year would schedule the possible text urls of the last year. This strategy wouldn't even guarantee that only finished texts are crawled, due to the fact that a text could be added during december and modified in january.
