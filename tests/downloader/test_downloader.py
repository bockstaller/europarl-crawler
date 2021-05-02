import pytest

from europarl.downloader import rewrite_links


def test_rewrite_links():
    base_url = "https://www.test.de"

    test_string = '<html><head><link href="styles.css" rel="stylesheet"></head><body><a href="/test">Testlink</a></body></html>'

    expected_string = '<html><head><link href="https://www.test.de/styles.css" rel="stylesheet"/></head><body><a href="https://www.test.de/test">Testlink</a></body></html>'

    result = rewrite_links(test_string, base_url)

    print(expected_string)
    print(result)

    assert result == expected_string
