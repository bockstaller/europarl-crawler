from datetime import date

import pytest

from europarl.rules.protocol import ProtocolEnHtmlRule, ProtocolEnPdfRule


@pytest.mark.parametrize(
    "date,expected",
    [
        (
            date(year=2019, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-9-2019-08-01_EN.pdf",
        ),
        (
            date(year=2014, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-8-2014-08-01_EN.pdf",
        ),
        (
            date(year=2009, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-7-2009-08-01_EN.pdf",
        ),
        (
            date(year=2004, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-6-2004-08-01_EN.pdf",
        ),
        (
            date(year=1999, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-5-1999-08-01_EN.pdf",
        ),
        (
            date(year=1994, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-4-1994-08-01_EN.pdf",
        ),
        (
            date(year=1989, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-3-1989-08-01_EN.pdf",
        ),
        (
            date(year=1984, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-2-1984-08-01_EN.pdf",
        ),
        (
            date(year=1979, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-1-1979-08-01_EN.pdf",
        ),
        (
            date(year=1950, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-0-1950-08-01_EN.pdf",
        ),
        (
            date(year=2025, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-0-2025-08-01_EN.pdf",
        ),
    ],
)
def test_get_url_protocol_en_pdf(date, expected):
    assert ProtocolEnPdfRule.url(date=date) == expected


@pytest.mark.parametrize(
    "date,expected",
    [
        (
            date(year=2019, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-9-2019-08-01_EN.html",
        ),
        (
            date(year=2014, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-8-2014-08-01_EN.html",
        ),
        (
            date(year=2009, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-7-2009-08-01_EN.html",
        ),
        (
            date(year=2004, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-6-2004-08-01_EN.html",
        ),
        (
            date(year=1999, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-5-1999-08-01_EN.html",
        ),
        (
            date(year=1994, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-4-1994-08-01_EN.html",
        ),
        (
            date(year=1989, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-3-1989-08-01_EN.html",
        ),
        (
            date(year=1984, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-2-1984-08-01_EN.html",
        ),
        (
            date(year=1979, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-1-1979-08-01_EN.html",
        ),
        (
            date(year=1950, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-0-1950-08-01_EN.html",
        ),
        (
            date(year=2025, month=8, day=1),
            "https://europarl.europa.eu/doceo/document/PV-0-2025-08-01_EN.html",
        ),
    ],
)
def test_get_url_protocol_en_html(date, expected):
    assert ProtocolEnHtmlRule.url(date) == expected
