from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class WordProtocolRule(Rule):
    """
    Base Rule for the different vesions of word protocol documents.
    """

    @classmethod
    def url(cls, date):
        """
        Creates word protocol urls based upon the date, language and file format

        Args:
            date (datetime.date): date to base the url of from

        Returns:
            str: url
        """
        document_url = (
            BASE_URL
            + "CRE-"
            + get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "_"
            + cls.language
            + cls.format
        )
        return document_url

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


@rule_registry
class WordProtocolEnPdfRule(WordProtocolRule):
    """
    Manages word protocol documents in English as PDF files
    """

    name = "word_protocol_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class WordProtocolEnHtmlRule(WordProtocolRule):
    """
    Manages Daily Agenda documents in English as HTML files
    """

    name = "word_protocol_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class WordProtocolDePdfRule(WordProtocolRule):
    """
    Manages Daily Agenda documents in German as PDF files
    """

    name = "word_protocol_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class WordProtocolDeHtmlRule(WordProtocolRule):
    """
    Manages Daily Agenda documents in German as HTML files
    """

    name = "word_protocol_de_html"
    format = ".html"
    language = "DE"
