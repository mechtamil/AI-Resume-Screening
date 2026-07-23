"""
Simple test for file utilities
"""

from utils.file_utils import get_extension


print(get_extension("resume.pdf"))

print(get_extension("candidate.docx"))

print(get_extension("sample.txt"))