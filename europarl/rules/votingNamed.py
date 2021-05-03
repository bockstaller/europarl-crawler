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
class NamedVotingFrPdfRule(NamedVotingRule):
    """
    Manages named voting documents in English as PDF files
    """

    name = "named_voting_fr_pdf"
    format = ".xml"
    language = "FR"


@rule_registry
class NamedVotingFrXMLRule(NamedVotingRule):
    """
    Manages named voting documents in English as HTML files
    """

    name = "named_voting_fr_xml"
    format = ".xml"
    language = "FR"
