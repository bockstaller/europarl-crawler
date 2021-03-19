Development setup
=================

Dependencies
------------

This project requires running installations of Postgres and Elasticsearch. They are configured automatically during start up of the application if the connections are setup correctly in the `settings.ini`-file. Meaning tables and indexes are created automatically during start up. Therefore a database user with appropriate rights should be used.

This repository makes setting up a dev environment easy by providing a Docker Compose setup that is operated via pipenv. The setup tutorial uses this method.

Setup
-----

#.  Install `docker <https://docs.docker.com/engine/install/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_.

#. | Install `pipenv <https://pipenv.pypa.io/en/latest/#install-pipenv-today>`_.
   | You might want to set ``export PIPENV_VENV_IN_PROJECT=1`` in your ``.bashrc/.zshrc`` for local virtual environments. Thereby you are making sure that all dependencies for your application are stored in the same directory under the ``.venv`` folder.

#. Clone repository into preferred directory (or simply download the source code and rename the folder as you like): ``git clone https://github.com/bockstaller/europarl-crawler``

#. Install packages: ``cd europarl-crawler && pipenv install --dev``

#. Activate virtual environment: ``pipenv shell``

#. Start the needed external services: ``pipenv run env_up``

#. Sanity check the ``settings.ini`` file. Especially the path configured in the ``[Downloader]`` section.

#. Run the tests: ``pipenv run test``

#. Build the documentation by running ``pipenv run docs_html`` or ``pipenv run docs_pdf``. The resulting documentation is stored in ``./docs/_build/...``. For PDF a local ``pdfTex`` installation is necessary.

#. Install Git hooks. `Installation <https://pre-commit.com/#installation>`_ and `Activation <https://pre-commit.com/#3-install-the-git-hook-scripts>`_ are described here.

#.  Use the CLI to run the crawler. Use ``eurocli --help`` to get guidance.

**Note:** To deactivate the environment again, run `pipenv run env_down` to tear down the elasticsearch and postgres services. An d run `deactivate` to leave the Python virtual environment.
