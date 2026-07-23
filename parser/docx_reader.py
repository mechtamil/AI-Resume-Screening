"""
==========================================================
AI Recruitment Assistant
Version : 0.2
Module  : DOCX Reader
==========================================================
"""

from docx import Document
import logging


def read_docx(file_path):
    """
    Reads a DOCX file and returns its text.
    """

    try:

        document = Document(file_path)

        text = ""

        for paragraph in document.paragraphs:

            if paragraph.text.strip():

                text += paragraph.text + "\n"

        logging.info(f"DOCX Read Successfully : {file_path}")

        return text

    except Exception as error:

        logging.error(f"Unable to read DOCX : {file_path}")

        logging.error(error)

        return ""