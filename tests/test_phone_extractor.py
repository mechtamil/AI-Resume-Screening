from parser.extractors.phone_extractor import PhoneExtractor

sample_resume = """
Ravi Kumar

Technical Writer

Email : ravi@gmail.com

Phone : +91 9876543210

Experience : 6 Years
"""

extractor = PhoneExtractor()

result = extractor.extract(sample_resume)

print()

print("Phone Extraction Result")

print("-----------------------")

print(result)