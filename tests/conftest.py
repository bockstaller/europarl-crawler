import configparser
import copy
import os

import pytest
from dotenv import load_dotenv
from psycopg2.sql import SQL, Identifier

from europarl.db import DBInterface, tables

TESTDB = "TEST_europarl_crawler"
TESTDB_TEMPLATE = TESTDB + "_TEMPLATE"


@pytest.fixture(scope="module")
def config():

    config = configparser.ConfigParser()
    config.read("settings.ini")
    print(os.getcwd())

    # Bootstrap by using configured Testing credentials
    config["DEFAULT"] = copy.deepcopy(config["Test"])
    config["Temp"] = copy.deepcopy(config["Test"])

    # extend config in memory with temporary test only extensions

    config["TestDB"] = {"DBName": TESTDB}
    config["TestDB_Template"] = {"DBName": TESTDB_TEMPLATE}
    config["DEFAULT"] = copy.deepcopy(config["TestDB"])
    return config


@pytest.fixture(scope="module")
def template_database_setup(request, config):
    """
    This test fixture manages the lifecycle of a template database
    containing empty tables of the application.
    This template database is created and dropped for every test module
    and is used by the db_interface-fixture as a template for creating a new
    database for every test.
    This template database is dropped and the db_connection closed after exiting the module.

    Args:
        request (pystest.request): manages fixture/test lifecycle

    Returns:
        DBInterface: returns a DBInterface to the template-database

    """

    temp_config = config["Temp"]

    temp_db = DBInterface(config=temp_config)

    with temp_db.cursor() as db:
        db.con.autocommit = True
        db.cur.execute(
            SQL("drop database if exists {db_name};").format(
                db_name=Identifier(TESTDB_TEMPLATE)
            )
        )
        db.cur.execute(
            SQL("create database {db_name};").format(
                db_name=Identifier(TESTDB_TEMPLATE)
            )
        )

    template_config = config["TestDB_Template"]

    template_db = DBInterface(config=template_config)

    for table in tables:
        table_inst = table(template_db)
        table_inst.create_table()

    def fin():
        template_db.connection.close()
        with temp_db.cursor() as db:
            db.cur.execute(
                SQL("drop database {db_name};").format(
                    db_name=Identifier(TESTDB_TEMPLATE)
                )
            )

        temp_db.connection.close()

    request.addfinalizer(fin)
    return template_db


@pytest.fixture
def db_interface(request, config, template_database_setup):
    """
    Creates a fresh database for every test by templating
    the template database from the tempalte_database_setup-fixture
    and dropping it after finishing the test.

    Args:
        template_database_setup (DBInterface): DBInterface to the template database
        request (pytest.request): manages fixture/test lifecycle

    Returns:
        [type]: [description]
    """

    template_db = template_database_setup

    with template_db.cursor() as db:
        db.con.autocommit = True
        db.cur.execute(
            SQL("drop database if exists {db_name};").format(db_name=Identifier(TESTDB))
        )
        db.cur.execute(
            SQL("create database {db_name} with template {template};").format(
                db_name=Identifier(TESTDB), template=Identifier(TESTDB_TEMPLATE)
            )
        )

    db_connection = DBInterface(config=config["TestDB"])

    def fin():
        db_connection.close()
        with template_db.cursor() as db:
            db.cur.execute(
                SQL("drop database {db_name};").format(db_name=Identifier(TESTDB))
            )

    request.addfinalizer(fin)

    return db_connection
