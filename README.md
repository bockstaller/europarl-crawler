# Europarl Crawler

This crawler crawls the website of the European Unions Parliament and stores the results in Elasticsearch.
It is part of an advanced software practical supervised by Prof. Dr. Michael Gertz.

## Introduction
The European Union publishes documents continuously, which record the daily business of the Union. One source for these documents is the European Parliament which publishes all of its documents here https://www.europarl.europa.eu/plenary/en/home.html. The website has a search functionality but doesn't publish all documents centrally to download them.

## Tasks
The main tasks for this document practical are:

Develop document data and metadata model
Implement the models in Elasticsearch
Implement an active Crawler or an RSS feed based data retrieval method
This should be implemented using Python and Elasticsearch

## Developing and Operations

### Dependencies

This project requires running installations of Postgres and Elasticsearch. They are configured automatically during start up of the application if the connections are setup correctly in the `settings.ini`-file. Meaning tables and indexes are created automatically during start up. Therefore a database user with appropriate rights should be used.

This repository makes setting up a dev environment easy by providing a Docker Compose setup that is operated via pipenv. The setup tutorial uses this method.

### Development Setup

1. [Install `docker`](https://docs.docker.com/engine/install/) and [`docker-compose`](https://docs.docker.com/compose/install/)

1. [Install](https://pipenv.pypa.io/en/latest/#install-pipenv-today) ```pipenv```. You might want to set ```export PIPENV_VENV_IN_PROJECT=1``` in your ```.bashrc/.zshrc``` for local virtual environments. Thereby you are making sure that all dependencies for your application are stored in the same directory under the `.venv` folder.

2. Clone repository into preferred directory (or simply download the source code and rename the folder as you like): `git clone https://github.com/bockstaller/europarl-crawler`

3. Install packages: `cd europarl-crawler && pipenv install --dev`

4. Activate virtual environment: `pipenv shell`

5. Start the needed external services: `pipenv run env_up`

6. Sanity check the `settings.ini` file. Especially the Path configured in the `[Downloader]`-section.

7. Run the tests: `pytest`

8. Build the documentation by running `pipenv run docs_html` or `pipenv run docs_pdf`. The resulting documentation is stored in `./docs/_build/...`. For PDF a local `pdfTex` installation is necessary.

8. Install Git hooks. They help you to execute tasks before your code is committed (see [Working with Git](#working-with-git)). Learn more about pre-commit in the [official docs](https://pre-commit.com/). ([Installation](https://pre-commit.com/#installation) and [Activation](https://pre-commit.com/#3-install-the-git-hook-scripts) are described here) In our case they are used to make sure that the application code is well formatted using [black](https://github.com/psf/black)/[autopep8](https://github.com/hhatto/autopep8), has no syntax errors using [flake8](https://gitlab.com/pycqa/flake8) and that the dependency imports are well sorted using [isort](https://github.com/PyCQA/isort). The pre-commit instructions are given by the `.pre-commit-config.yaml`. Any isort specific settings are given by the `.isort.cfg` file.

9.  Use the CLI to run the crawler. Use `eurocli --help` to get guidance.

**Note:** To deactivate the environment again, run `pipenv run env_down` to tear down the elasticsearch and postgres services. An d run `deactivate` to leave the Python virtual environment.


### Running the software

Follow the steps outlined in the development setup section of this document and adapt the `settings.ini` file to your requirements.

#### Configuration

The application can be configured via a settings.ini file. It contains all settings that are used per application module.

Defaults can be overidden by a custom configuration file stored in "/etc/europarl/settings.ini".

The configuration module leverages the Python configparser module and its default value functionality. Therefore all values in the DEFAULT section of the configuration file are used in the other sections where these values are not entered.

```ini
[DEFAULT]
# Loglevel
LogLevel=INFO

# Sleeptime before a worker calls its main function again
DefaultPollingTimeout=0.1

# Database Connection Settings
DBName=europarl
DBUser=postgres
DBPassword=
DBHost=localhost
DBPort=5432

# Amount of entries the batch processing worker should preload
PrefetchLimit = 5

# Amount of seconds to wait on the cleanup jobs before killing the process
StopWaitSecs=10

[General]
# Loglevel
# LogLevel=INFO

[TokenBucketWorker]
# Loglevel
# LogLevel=INFO

# Minimal interval between token generation in seconds
MinIntervalSecs = 3

# ThrottlingFactor x IntervalSecs = Time to wait before making the next throttling check
ThrottlingFactor = 10

[SessionDayChecker]
# Loglevel
# LogLevel=INFO

# Amount of entries the batch processing worker should preload
# PrefetchLimit = 5

[DateUrlGenerator]
# Loglevel
# LogLevel=INFO

# Amount of entries the batch processing worker should preload
# PrefetchLimit = 5

[Downloader]
# Loglevel
# LogLevel=INFO

# Amount of Worker Instances
Instances=1
# Directory where documents are stored
Path=/Volumes/Backup/data/

# Amount of seconds to wait on the cleanup jobs before killing the process
#StopWaitSecs=10

# RequestTimeoutFactor x StopWaitSeconds = Amount of seconds until a request is classified as a timeout
RequestTimeoutFactor = 0.75

[PostProcessingScheduler]
# Loglevel
# LogLevel=INFO

# Amount of entries the batch processing worker should preload
# PrefetchLimit = 5


[PostProcessingWorker]
# Loglevel
# LogLevel=INFO

# Amount of Worker Instances
Instances=6


[Indexer]
# Loglevel
# LogLevel=INFO

# Amount of entries the batch processing worker should preload
# PrefetchLimit = 5

# Elasticsearch Settings
ESConnection=localhost:9200
ESIndexname=europarl

[Test]
# Database Connection Settings for tests
# DBName=europarl
# DBUser=postgres
# DBPassword=
# DBHost=localhost
# DBPort=5432

# Elasticsearch Settings for tests
# ESConnection=localhost:9200
# ESIndexname=europarl
```

#### Installation

Then add these three `systemd` services to your setup. Replacing the `[...]` in the templates with path to the interpreter with the installed europarl project. Logs are then available via `journalctl`.
The services are meant to restart every 24 hours. Test runs didn't produced any errors caused by long running processes, but restarts don't hurt the progress made.


#### Crawler

```systemd
[Unit]
Description=Crawler
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RuntimeMaxSec=86400
RestartSec=1
User=europarl
ExecStart=[...]/python3.9 eurocli crawler start

[Install]
WantedBy=multi-user.target
```
#### Postprocessor

```systemd
[Unit]
Description=Postprocessor
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RuntimeMaxSec=86400
RestartSec=1
User=europarl
ExecStart=[...]/python3.9 eurocli postprocessing start

[Install]
WantedBy=multi-user.target
```

#### Indexer

```systemd
[Unit]
Description=Indexer
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RuntimeMaxSec=86400
RestartSec=1
User=europarl
ExecStart=[...]/python3.9 eurocli indexing start

[Install]
WantedBy=multi-user.target
```

### Operations

The running application can be controlled via a CLI which uses the same configuration file to interact with the database and elasticsearch. "--help" can be used in addition to the listed commands to get an explanation of what the commands do.

#### Rules
`eurocli rules`
Lists all currently registred rules, their id's, language, and fileformat in a table

`eurocli rules -r 1 --activate/--deactivate`
Enables/Disables the rule with the id passed with the -r parameter

#### Crawler
`eurocli crawler start`
Starts the crawler job

#### Postprocessing
`eurocli postprocessing start`
Starts the postprocessing job

`eurocli postprocessing reset -r 1`
Clears the postprocessing resets for the passed rule and unindexes all postprocessing results from Elasticsearch. The indexed bit is only reset for documents where this unindexing was successful.

`eurocli postprocessing reset -r 1 -f`
Clears the postprocessing resets for the passed rule and unindexes all postprocessing results from Elasticsearch. The indexed bit is reset for all documents associated with this rule.

#### Indexing
`eurocli indexing start`
Starts the indexing job

`eurocli indexing unindex`
Retries the unindexing operation from "eurocli postprocessing reset -r 1"

`eurocli indexing reindex /path/to/new/mapping.json`
Creates a new index based upon the passed mapping, transfers all old entries to the new index and reroutes the running indexing operation to the new index.