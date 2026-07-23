
from database.database import Database

db = Database()

db.create_tables()

print("RecruitOS Database Created Successfully.")

db.close()