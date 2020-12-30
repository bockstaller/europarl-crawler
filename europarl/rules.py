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
    return protocol_url(
        language=session_day.language, format=session_day.format, date=date
    )


session_day.format = ".pdf"
session_day.language = "EN"


@register_rule
def protocol_en_pdf(date):
    return protocol_url(
        language=protocol_en_pdf.language, format=protocol_en_pdf.format, date=date
    )


protocol_en_pdf.format = ".pdf"
protocol_en_pdf.language = "EN"


@register_rule
def protocol_en_html(date):
    return protocol_url(
        language=protocol_en_html.language, format=protocol_en_html.format, date=date
    )


protocol_en_html.format = ".html"
protocol_en_html.language = "EN"


@register_rule
def protocol_de_pdf(date):
    return protocol_url(
        language=protocol_de_pdf.language, format=protocol_de_pdf.format, date=date
    )


protocol_de_pdf.format = ".pdf"
protocol_de_pdf.language = "DE"


@register_rule
def protocol_de_html(date):
    return protocol_url(
        language=protocol_de_html.language, format=protocol_de_html.format, date=date
    )


protocol_de_html.format = ".html"
protocol_de_html.language = "DE"


def word_protocol_url(language, format, date):
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
    return word_protocol_url(
        language=word_protocol_en_pdf.language,
        format=word_protocol_en_pdf.format,
        date=date,
    )


word_protocol_en_pdf.format = ".pdf"
word_protocol_en_pdf.language = "EN"


@register_rule
def word_protocol_en_html(date):
    return word_protocol_url(
        language=word_protocol_en_html.language,
        format=word_protocol_en_html.format,
        date=date,
    )


word_protocol_en_html.format = ".html"
word_protocol_en_html.language = "EN"


@register_rule
def word_protocol_de_pdf(date):
    return word_protocol_url(
        language=word_protocol_de_pdf.language,
        format=word_protocol_de_pdf.format,
        date=date,
    )


word_protocol_de_pdf.format = ".pdf"
word_protocol_de_pdf.language = "DE"


@register_rule
def word_protocol_de_html(date):
    return word_protocol_url(
        language=word_protocol_de_html.language,
        format=word_protocol_de_html.format,
        date=date,
    )


word_protocol_de_html.format = ".html"
word_protocol_de_html.language = "DE"
