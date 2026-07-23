from parser.extractors.email_extractor import EmailExtractor

sample_resume = """
Ravi Kumar

Senior Technical Writer

Email : Ravi.Kumar@Gmail.com

Phone : 9876543210

Skills

DITA

XML

Python
"""

extractor = EmailExtractor()

result = extractor.extract(sample_resume)

print()

print("Email Extraction Result")

print("-----------------------")

print(result)
