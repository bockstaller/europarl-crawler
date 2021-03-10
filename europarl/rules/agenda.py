from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class DailyAgenda(Rule):
    @classmethod
    def url(cls, date):
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
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data


@rule_registry
class DailyAgendaEnPdfRule(DailyAgenda):
    name = "daily_agenda_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class DailyAgendaEnHtmlRule(DailyAgenda):
    name = "daily_agenda_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class DailyAgendaDePdfRule(DailyAgenda):
    name = "daily_agenda_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class DailyAgendaDeHtmlRule(DailyAgenda):
    name = "daily_agenda_de_html"
    format = ".html"
    language = "DE"


class Agenda(Rule):
    @classmethod
    def url(cls, date):
        document_url = (
            BASE_URL
            + "OJ-"
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
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data


@rule_registry
class AgendaEnPdfRule(Agenda):
    name = "daily_agenda_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class AgendaEnHtmlRule(Agenda):
    name = "agenda_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class AgendaDePdfRule(Agenda):
    name = "agenda_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class AgendaDeHtmlRule(Agenda):
    name = "agenda_de_html"
    format = ".html"
    language = "DE"
