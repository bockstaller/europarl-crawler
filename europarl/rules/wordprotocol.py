from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class WordProtocolRule(Rule):
    @classmethod
    def url(cls, date):
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
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data


@rule_registry
class WordProtocolEnPdfRule(WordProtocolRule):
    name = "word_protocol_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class WordProtocolEnHtmlRule(WordProtocolRule):
    name = "word_protocol_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class WordProtocolDePdfRule(WordProtocolRule):
    name = "word_protocol_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class WordProtocolDeHtmlRule(WordProtocolRule):
    name = "word_protocol_de_html"
    format = ".html"
    language = "DE"
