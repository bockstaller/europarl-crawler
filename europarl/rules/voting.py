from europarl.rules.extraction import filecontent, filesize
from europarl.rules.rule import BASE_URL, Rule, get_term, rule_registry


class VotingOverviewRule(Rule):
    @classmethod
    def url(cls, date):
        document_url = (
            BASE_URL
            + "PV-"
            + get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "-"
            + "VOT"
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
class VotingOverviewEnPdfRule(VotingOverviewRule):
    name = "voting_overview_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class VotingOverviewDePdfRule(VotingOverviewRule):
    name = "voting_overview_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class VotingOverviewEnHtmlRule(VotingOverviewRule):
    name = "voting_overview_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class VotingOverviewDeHtmlRule(VotingOverviewRule):
    name = "voting_overview_de_Html"
    format = ".html"
    language = "DE"


class NamedVotingRule(Rule):
    @classmethod
    def url(cls, date):
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
        data = {}
        data.update(filesize(filepath))
        data.update(filecontent(filepath, cls.format))
        return data


@rule_registry
class NamedVotingEnPdfRule(NamedVotingRule):
    name = "named_voting_en_pdf"
    format = ".pdf"
    language = "EN"


@rule_registry
class NamedVotingDePdfRule(NamedVotingRule):
    name = "named_overview_de_pdf"
    format = ".pdf"
    language = "DE"


@rule_registry
class NamedVotingEnHtmlRule(NamedVotingRule):
    name = "named_voting_en_html"
    format = ".html"
    language = "EN"


@rule_registry
class NamedVotingDeHtmlRule(NamedVotingRule):
    name = "named_overview_de_html"
    format = ".html"
    language = "DE"
