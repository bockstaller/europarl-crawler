import logging
import os
from abc import ABC
from datetime import date

BASE_URL = "https://europarl.europa.eu/doceo/document/"


def makeRuleRegistry():
    registry = {}

    def registrar(cls):
        registry[cls.name] = cls
        return cls

    registrar.all = registry
    registrar.keys = registry.keys()

    return registrar


rule_registry = makeRuleRegistry()


def get_term(day) -> str:
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
    language = None
    format = None

    @classmethod
    def extract_data(cls, filepath):
        raise NotImplementedError

    @classmethod
    def url(cls, date):
        raise NotImplementedError
