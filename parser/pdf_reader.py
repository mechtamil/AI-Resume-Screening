"""
==========================================================
AI Recruitment Assistant
Version : 0.2
Module  : PDF Reader
==========================================================
"""

import fitz
import logging


def read_pdf(file_path):
    """
    Reads a PDF file and returns its text.

    Parameters
    ----------
    file_path : str

    Returns
    -------
    str
    """

    try:

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        logging.info(f"PDF Read Successfully : {file_path}")

        return text

    except Exception as error:

        logging.error(f"Unable to read PDF : {file_path}")

        logging.error(error)

        return ""