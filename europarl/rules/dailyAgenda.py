from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class DailyAgenda(Rule):
    """
    Base Rule for the different vesions of daily agenda documents.
    """

    @classmethod
    def url(cls, date):
        """
        Creates daily agenda urls based upon the date, language and file format

        Args:
            date (datetime.date): date to base the url of from

        Returns:
            str: url
        """
        document_url = (
            BASE_URL
            + "OJQ-"
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
class DailyAgendaEnPdfRule(DailyAgenda):
    """
    Manages Daily Agenda documents in English as PDF files
    """

    name = "daily_agenda_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class DailyAgendaEnHtmlRule(DailyAgenda):
    """
    Manages Daily Agenda documents in English as HTML files
    """

    name = "daily_agenda_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class DailyAgendaDePdfRule(DailyAgenda):
    """
    Manages Daily Agenda documents in German as PDF files
    """

    name = "daily_agenda_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class DailyAgendaDeHtmlRule(DailyAgenda):
    """
    Manages Daily Agenda documents in German as HTML files
    """

    name = "daily_agenda_de_html"
    format = ".html"
    language = "DE"
