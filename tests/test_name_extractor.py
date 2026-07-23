from parser.extractors.name_extractor import NameExtractor

sample_resume = """

Ravi Kumar

Senior Technical Writer

Email:
ravi@gmail.com

Phone:
9876543210

Experience
6 Years

Skills

DITA
XML
Arbortext
Python

"""

extractor = NameExtractor()

name = extractor.extract(sample_resume)

print()

print("Candidate Name:")

print(name)