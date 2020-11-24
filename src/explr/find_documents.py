import csv
from datetime import date, timedelta

import requests
from fake_headers import Headers
from requests_futures import sessions

base_url = "https://europarl.europa.eu/doceo/document/"
filename = "urls.csv"

terms = [
    [4, date(1994, 7, 1), date(1999, 7, 31)],
    [5, date(1999, 7, 1), date(2004, 7, 31)],
    [6, date(2004, 7, 1), date(2009, 7, 31)],
    [7, date(2009, 7, 1), date(2014, 7, 31)],
    [8, date(2014, 7, 1), date(2019, 7, 31)],
    [9, date(2019, 7, 1), date(2024, 7, 31)],
]


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


with open(filename, "w", newline="") as csvfile:
    fieldnames = [
        "pdf_url",
        "pdf_status_code",
        "pdf_content_length",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

session = sessions.FuturesSession(max_workers=4)

urls = []

for term in terms:
    for single_date in daterange(term[1], term[2]):

        document_url = (
            base_url
            + "PV-"
            + str(term[0])
            + "-"
            + single_date.strftime("%Y-%m-%d")
            + "_EN"
        )

        pdf_url = document_url + ".pdf"

        urls.append(pdf_url)


futures = []

for url in urls:
    futures.append(session.head(url, allow_redirects=True))

for f in futures:
    resp = f.result()
    print(resp.status_code)
    if resp.status_code == 200:
        with open(filename, "a", newline="") as csvfile:
            urlwriter = csv.writer(csvfile)

            urlwriter.writerow(
                [
                    resp.url,
                    resp.status_code,
                    resp.headers.get("content-length", 0),
                ]
            )
