import io
from datetime import date

import pytest

from europarl.rules.protocol import ProtocolEnHtmlRule, ProtocolEnPdfRule
from europarl.rules.rule import Rule, get_term, rule_registry


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
    assert get_term(date) == expected


@pytest.mark.parametrize(
    "name, language, format, raises",
    [
        ("a", "b", None, True),
        ("a", None, "c", True),
        (None, "b", "c", True),
        ("a", "b", "c", False),
    ],
)
def test_rule(name, language, format, raises):
    """
    Tests that an appropriate NotImplementedError
    is raised if a necessary attribute isn't set.

    Args:
        name (str): name to be set
        language (str): language string to be set
        format (str): format to be set
        raises (boolean): boolean if an exception is expected or not
    """
    R = Rule
    R.name = name
    R.language = language
    R.format = format

    if raises:
        with pytest.raises(NotImplementedError):
            R()
    else:
        R()


@pytest.mark.parametrize("rule", rule_registry.keys)
def test_rule_url_implemented(rule):
    """
    Tests that all registered rules have an url
    function implemented that returns the correct datatype.

    Args:
        rule (str): rulename
    """
    r = rule_registry.all[rule]
    d = date(1979, 7, 1)
    result = r.url(d)
    assert type(result) == str


@pytest.mark.parametrize("rule", rule_registry.keys)
def test_rule_extract_data_implemented(rule):
    """
    Tests that all registered rules have an extract_data
    function implemented that returns the correct datatype.

    Args:
        rule (str): rulename
    """
    r = rule_registry.all[rule]
    f = io.StringIO("some initial text data")
    result = r.extract_data(f)
    assert type(result) == dict
