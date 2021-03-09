from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class ProtocolRule(Rule):
    @classmethod
    def extract_data(cls, filepath):
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data

    @classmethod
    def url(cls, date):
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
    name = "session_day"
    format = ".pdf"
    language = "EN"


@rule_registry
class ProtocolEnPdfRule(ProtocolRule):
    name = "protocol_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class ProtocolEnHtmlRule(ProtocolRule):
    name = "protocol_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class ProtocolDePdfRule(ProtocolRule):
    name = "protocol_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class ProtocolDeHtmlRule(ProtocolRule):
    name = "protocol_de_html"
    format = ".html"
    language = "DE"
