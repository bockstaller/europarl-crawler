import codecs
import logging
import os

from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text


def filesize(filepath):
    try:
        res = os.path.getsize(filepath)
    except Exception as e:
        logging.error(e)
        res = None
    return {"filesize": res}


def filecontent(filepath, format):
    try:
        if format == ".html":
            with open(filepath, "r") as file:
                soup = BeautifulSoup(file.read(), "html.parser")
                text = soup.get_text()
        elif format == ".pdf":
            text = extract_text(filepath)
        else:
            text = None
    except Exception as e:
        logging.error(e)
        text = None

    return {"content": text}
