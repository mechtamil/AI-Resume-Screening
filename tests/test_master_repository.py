from services.master_repository import MasterRepository

from config.sheet_names import SKILLS
from config.sheet_names import SCORING


print()

print("=" * 60)

print("RecruitOS Master Repository Test")

print("=" * 60)

MasterRepository.validate_workbook()

print()

print("Workbook Validated")

print()

print("Available Sheets")

print("---------------------------")

for sheet in MasterRepository.list_sheets():

    print(sheet)

print()

print("=" * 60)

print("Skills Sheet")

print("=" * 60)

skills = MasterRepository.get_sheet(SKILLS)

print(skills)

print()

print("=" * 60)

print("Scoring Sheet")

print("=" * 60)

scoring = MasterRepository.get_sheet(SCORING)

print(scoring)

print()

print("=" * 60)

print("Workbook Information")

print("=" * 60)

MasterRepository.display_info()