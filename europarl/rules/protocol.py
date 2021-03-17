from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class ProtocolRule(Rule):
    """
    Base Rule for the different vesions of protocol documents.
    """

    @classmethod
    def extract_data(cls, filepath):
        """
        Extracts the filesize and filecontent of a passed in file

        Args:
            filepath (str): path to the file

        Returns:
            dict: dictionary containing filesize and content of the the document
        """
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data

    @classmethod
    def url(cls, date):
        """
        Creates protocol urls based upon the date, language and file format

        Args:
            date (datetime.date): date to base the url of from

        Returns:
            str: url
        """
        document_url = (
            BASE_URL
            + "PV-"
            + get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "_"
            + cls.language
            + cls.format
        )
        return document_url


@rule_registry
class SessionDayRule(ProtocolRule):
    """
    Special rule used to create urls to determine if a session occured on a given day.
    """

    name = "session_day"
    format = ".pdf"
    language = "EN"


@rule_registry
class ProtocolEnPdfRule(ProtocolRule):
    """
    Manages protocol documents in English as PDF files
    """

    name = "protocol_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class ProtocolEnHtmlRule(ProtocolRule):
    """
    Manages protocol documents in English as HTML files
    """

    name = "protocol_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class ProtocolDePdfRule(ProtocolRule):
    """
    Manages protocol documents in German as PDF files
    """

    name = "protocol_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class ProtocolDeHtmlRule(ProtocolRule):
    """
    Manages protocol documents in German as HTML files
    """

    name = "protocol_de_html"
    format = ".html"
    language = "DE"
