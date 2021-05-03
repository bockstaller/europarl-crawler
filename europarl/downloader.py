import datetime
import logging
import os
import time
import urllib
from pathlib import Path

import bs4
import requests

from europarl import rules

logger = logging.getLogger("eurocli")


def get_unviewed_date(directory, date):
    ledger = os.path.join(directory, "backfilled_dates.txt")

    myfile = Path(ledger)
    myfile.touch(exist_ok=True)

    with open(ledger, mode="r+") as f:
        backfilled_dates = [line.strip() for line in f if line]

    sdate = date
    edate = datetime.date(1979, 7, 1)
    delta = sdate - edate

    for i in range(delta.days + 1):
        day = sdate - datetime.timedelta(days=i)
        if day.strftime("%Y-%m-%d") in backfilled_dates:
            next
        else:
            return day

    return None


def spaced_out_dates(date):
    """
    Returns a list of dates starting from date going back to the past.
    Older dates are not as common.

    Args:
        date (datetime): date to start from

    Returns:
        [date]: list of dates
    """

    spacing_groups = [
        (range(0, 14), 1),
        (range(14, 28), 2),
        (range(28, 84), 5),
        (range(84, 365), 10),
    ]

    dates = []

    for spacing in spacing_groups:
        for i in spacing[0]:
            if i % spacing[1] == 0:
                dates.append(date - datetime.timedelta(days=i))

    for i in range(1, 4):
        dates.append(date - datetime.timedelta(days=i * 100))

    return dates


def scrape_document(basedir, rule, date, session, retry=3, sleep=3):
    """
    Download and store a document
    """
    logger.debug("{}: Scraping {}".format(date.strftime("%Y-%m-%d"), rule.name))
    url = rule.url(date)
    logger.debug("{}: Using {}".format(date.strftime("%Y-%m-%d"), url))

    for i in range(0, retry):
        try:
            logger.debug(
                "{}: Attempt {} from {}".format(date.strftime("%Y-%m-%d"), i, retry)
            )
            resp = session.get(
                url,
                allow_redirects=True,
                timeout=sleep,
            )

            if resp.status_code == 200:
                logger.debug("{}: Success".format(date.strftime("%Y-%m-%d")))
                break
            else:
                time.sleep(sleep)
        except requests.exceptions.ReadTimeout:
            time.sleep(sleep)

    if rule.format == ".html":
        html = rewrite_links(html=resp.text, base_url=rules.BASE_URL)
        logger.debug("{}: Links rewrote".format(date.strftime("%Y-%m-%d")))

    filepath = rule.store_document(basedir, date, html)
    logger.debug("{}: File saved: {}".format(date.strftime("%Y-%m-%d"), filepath))

    time.sleep(sleep)
    logger.debug("{}: Sleeping".format(date.strftime("%Y-%m-%d")))


def rewrite_links(html, base_url):
    soup = bs4.BeautifulSoup(html, "lxml")
    links = soup.find_all(href=True)
    for link in links:
        if not bool(urllib.parse.urlparse(link.attrs["href"]).netloc):
            if not link.attrs["href"][0] == "#":
                new_url = urllib.parse.urljoin(base_url, link.attrs["href"])
                link.attrs["href"] = new_url

    sources = soup.findAll("script", {"src": True})
    for src in sources:
        if not bool(urllib.parse.urlparse(src.attrs["src"]).netloc):
            new_url = urllib.parse.urljoin(base_url, src.attrs["src"])
            src.attrs["src"] = new_url

    return str(soup)


def download_all_docs(basedir, rulenames, date, retry, sleep):
    with requests.Session() as ses:
        rule = rules.rule_registry.all["session_day"]
        url = rule.url(date)

        resp = ses.get(
            url,
            allow_redirects=True,
            timeout=sleep,
        )

        if resp.status_code == 404:
            logger.info(
                "{}: No protocol found - skipping.".format(date.strftime("%Y-%m-%d"))
            )
            time.sleep(sleep)
            return

        for rulename in rulenames:
            rule = rules.rule_registry.all[rulename]
            if rule.document_type == rule.SESSION_DOC:
                scrape_document(
                    basedir=basedir,
                    rule=rule,
                    date=date,
                    session=ses,
                    retry=retry,
                    sleep=sleep,
                )

    return
