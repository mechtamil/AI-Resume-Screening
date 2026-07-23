
from models.resume import Resume


resume = Resume()

resume.file_name = "Ravi.pdf"

resume.file_type = ".pdf"

resume.file_size = 456321

resume.page_count = 5

resume.extracted_text = """
Python XML DITA FrameMaker Volvo
"""

resume.calculate_statistics()

resume.mark_processed()

resume.display()

print()

print(resume.summary())