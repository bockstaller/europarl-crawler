from datetime import date

from .rule import Rule


class Protocol(Rule):
    @classmethod
    def get_url(cls, date: date) -> str:
        document_url = (
            cls.BASE_URL
            + "PV-"
            + cls.get_term(date)
            + "-"
            + date.strftime("%Y-%m-%d")
            + "_EN"
            + ".pdf"
        )
        return document_url
