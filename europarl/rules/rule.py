import logging
import os
from abc import ABC
from datetime import date
from pathlib import Path

BASE_URL = "https://europarl.europa.eu/doceo/document/"


def make_rule_registry():
    """
    Creates the rule registry that runs on import time
    and collects all rules marked with the @rule_registry
    decorator

    Returns:
        function: Function to register a new rule
    """
    registry = {}

    def registrar(cls):
        registry[cls.name] = cls
        return cls

    registrar.all = registry
    registrar.keys = registry.keys()

    return registrar


rule_registry = make_rule_registry()


def get_term(day):
    """
    Matches the european parliaments election term to a given date.
    Necessary to generate a protocol-URL

    Args:
        date (datetime.date): Date for which the term is needed

    Returns:
        str: number of the election term as a string
    """

    terms = {
        "1": [date(1979, 7, 1), date(1984, 7, 31)],
        "2": [date(1984, 7, 1), date(1989, 7, 31)],
        "3": [date(1989, 7, 1), date(1994, 7, 31)],
        "4": [date(1994, 7, 1), date(1999, 7, 31)],
        "5": [date(1999, 7, 1), date(2004, 7, 31)],
        "6": [date(2004, 7, 1), date(2009, 7, 31)],
        "7": [date(2009, 7, 1), date(2014, 7, 31)],
        "8": [date(2014, 7, 1), date(2019, 7, 31)],
        "9": [date(2019, 7, 1), date(2024, 7, 31)],
    }

    for key, term in terms.items():
        if term[0] < day < term[1]:
            return key
    return "0"


class Rule(ABC):
    """
    Abstract base class for the rules.

    A derived class has to provide the attributes
    name, language, and format with values and has
    to implement the functions extract_data() and url()

    Raises:
        NotImplementedError: If name, language, format, extract_data() or url() are not set up
    """

    SESSION_DOC = "session_document"
    TEXT_DOC = "text_document"

    name = None
    language = None
    format = None
    document_type = SESSION_DOC

    def __init__(self):
        if self.name is None:
            raise NotImplementedError(
                "Rule {} has no name attribute".format(self.__class__.__name__)
            )
        if self.language is None:
            raise NotImplementedError(
                "Rule {} has no language attribute".format(self.__class__.__name__)
            )
        if self.format is None:
            raise NotImplementedError(
                "Rule {} has no format attribute".format(self.__class__.__name__)
            )

    @classmethod
    def store_document(cls, basedir, date, html):
        dirpath = cls.get_filepath(basedir, date)
        dirpath.mkdir(parents=True, exist_ok=True)
        filepath = dirpath.joinpath(cls.get_filename())
        with filepath.open(mode="w") as f:
            f.write(html)
        return filepath

    @classmethod
    def get_filepath(cls, basedir, date):
        return Path(basedir).joinpath(date.strftime("%Y-%m-%d"))

    @classmethod
    def get_filename(cls):
        return cls.name + cls.format

    @classmethod
    def extract_data(cls, filepath):
        """
        Not implemented data extraction function.
        All extracted data get's appended to a common dictionary and must
        be returned. Failures should be logged and failed data should be set to None.
        It might be necessary to namespace the dictionary keys to
        avoid overwriting information.

        The test tests.rules.test_rule.test_rule_extract_data_implemented(rule)
        checks that all registred rules return a dictionary when this function
        is called.

        Args:
            filepath (str): Path to the file to extract data from

        Raises:
            NotImplementedError: Function must be implemented

        Returns:
            dict: dict of all extracted data
        """
        raise NotImplementedError
        return {}

    @classmethod
    def url(cls, date):
        """
        Not implemented url generation function.
        Must generate a url as a string from a passed in datetime.date objection.

        The test tests.rules.test_rule.test_rule_url_implemented(rule)
        checks that all registred rules return a dictionary when this function
        is called.

        Args:
            date (datetime.date): Date to base the url of from

        Raises:
            NotImplementedError: Function must be implemented

        Returns:
            str: url as a string
        """
        raise NotImplementedError
        return ""

    @classmethod
    def save_document(cls, date):
        raise NotImplementedError
