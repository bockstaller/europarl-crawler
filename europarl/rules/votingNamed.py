from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class NamedVotingRule(Rule):
    """
    Base Rule for the different vesions of named voting documents.
    """

    @classmethod
    def url(cls, date):
        """
        Creates named voting urls based upon the date, language and file format

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
            + "-"
            + "RCV"
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
class NamedVotingEnPdfRule(NamedVotingRule):
    """
    Manages named voting documents in English as PDF files
    """

    name = "named_voting_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class NamedVotingDePdfRule(NamedVotingRule):
    """
    Manages named voting documents in German as PDF files
    """

    name = "named_overview_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class NamedVotingEnHtmlRule(NamedVotingRule):
    """
    Manages named voting documents in English as HTML files
    """

    name = "named_voting_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class NamedVotingDeHtmlRule(NamedVotingRule):
    """
    Manages named voting documents in German as HTML files
    """

    name = "named_overview_de_html"
    format = ".html"
    language = "DE"
