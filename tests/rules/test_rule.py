from datetime import date

import pytest

from europarl.rules import Rule


@pytest.mark.parametrize(
    "date,expected",
    [
        (date(year=2019, month=8, day=1), "9"),
        (date(year=2014, month=8, day=1), "8"),
        (date(year=2009, month=8, day=1), "7"),
        (date(year=2004, month=8, day=1), "6"),
        (date(year=1999, month=8, day=1), "5"),
        (date(year=1994, month=8, day=1), "4"),
        (date(year=1989, month=8, day=1), "3"),
        (date(year=1984, month=8, day=1), "2"),
        (date(year=1979, month=8, day=1), "1"),
        (date(year=1950, month=8, day=1), "0"),
        (date(year=2025, month=8, day=1), "0"),
    ],
)
def test_get_term(date, expected):
    assert Rule.get_term(date) == expected
