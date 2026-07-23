from database.candidate_repository import CandidateRepository

repo = CandidateRepository()

repo.add_candidate(
    full_name="Ravi Kumar",
    email="ravi@gmail.com",
    phone="9876543210",
    experience=6.5,
    current_company="Volvo",
    location="Bangalore",
    notice_period="30 Days",
    current_ctc="10 LPA",
    expected_ctc="13 LPA"
)

print()

print("Candidate Added Successfully")

print()

print("Total Candidates :", repo.get_candidate_count())

print()

print("Candidate List")

print("------------------------------")

for row in repo.get_all_candidates():

    print(row)

repo.close()