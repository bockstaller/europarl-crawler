from .rule import Rule


class Protocol(Rule):
    format = ""

    @classmethod
    def use_rule(cls, date):
        document_url = (
            cls.BASE_URL
            + "PV-"
            + cls.get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "_EN"
            + cls.format
        )
        return document_url

    def get_url(self, date):
        return {
            "rule_id": self.id,
            "url": self.use_rule(date["date"]),
            "date": date["date"],
            "date_id": date["date_id"],
        }


class PdfProtocol(Protocol):
    format = ".pdf"


class HtmlProtocol(Protocol):
    format = ".html"
