"""
============================================================
RecruitOS
TXT Reader
Version : 0.6
Author  : Tamilvanan A

Description:
Reads text files and returns the content.
============================================================
"""


def read_txt(file_path: str) -> str:
    """
    Read a TXT file and return its content.

    Args:
        file_path (str): Path to the text file.

    Returns:
        str: File content.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()