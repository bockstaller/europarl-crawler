from datetime import date

RULES = dict()
BASE_URL = "https://europarl.europa.eu/doceo/document/"


def register_rule(func):
    """Register a function as a rule"""
    RULES[func.__name__] = func

    return func


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


def protocol_url(language, format, date):
    document_url = (
        BASE_URL
        + "PV-"
        + get_term(date)
        + "-"
        + date.strftime("%Y-%m-%d")
        + "_"
        + language
        + format
    )
    return document_url


@register_rule
def session_day(date):
    return protocol_url(language="EN", format=".pdf", date=date)


@register_rule
def protocol_en_pdf(date):
    return protocol_url(language="EN", format=".pdf", date=date)


@register_rule
def protocol_en_html(date):
    return protocol_url(language="EN", format=".html", date=date)


@register_rule
def protocol_de_pdf(date):
    return protocol_url(language="DE", format=".pdf", date=date)


@register_rule
def protocol_de_html(date):
    return protocol_url(language="DE", format=".html", date=date)


def word_protocol_url(language, formatt, date):
    document_url = (
        BASE_URL
        + "CRE-"
        + get_term(date)
        + "-"
        + date.strftime("%Y-%m-%d")
        + "_"
        + language
        + format
    )
    return document_url


@register_rule
def word_protocol_en_pdf(date):
    return word_protocol_url(language="EN", format=".pdf", date=date)


@register_rule
def word_protocol_en_html(date):
    return word_protocol_url(language="EN", format=".html", date=date)


@register_rule
def word_protocol_de_pdf(date):
    return word_protocol_url(language="DE", format=".pdf", date=date)


@register_rule
def word_protocol_de_html(date):
    return word_protocol_url(language="DE", format=".html", date=date)
