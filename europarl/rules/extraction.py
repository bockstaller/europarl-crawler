import codecs
import logging
import os

from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text


def filesize(filepath):
    """
    Returns the filesize of a document given a filepath.

    Args:
        filepath (str): path to the file

    Returns:
        dict: dictionary with the single key "filesize" and an integer as a value
    """
    try:
        res = os.path.getsize(filepath)
    except Exception as e:
        logging.error(e)
        res = None
    return {"filesize": res}


def filecontent(filepath, format):
    """
    Returns the content contained in a HTML or PDF file.


    Args:
        filepath (str): path to the file
        format (str): string containing the file ending

    Returns:
        dict: dictionary with the single key "content" and a string containing the files content as the value
    """
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
