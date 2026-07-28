"""Shared test helpers for authenticated RecruitOS repository tests."""
from __future__ import annotations

import hashlib
from unittest.mock import patch
from pathlib import Path

from models.security_context import SecurityContext
from services.auth_service import AuthService
from services.authorization_service import SYSTEM_OWNER, USER
from services.user_management_service import UserManagementService

TEST_PASSWORD = "Correct Horse Battery 123!"
TEST_TEMPORARY_PASSWORD = "Temp@123"
# Automated-test-only value. This is not a deployment secret.
TEST_SETUP_KEY = "RecruitOS-Automated-Test-Setup-Key"

TEST_OWNER_USER_ID = "TEST-SYSTEM-OWNER"
TEST_OWNER_EMAIL = "system.owner@recruitos.test"
TEST_LOCATION = "India - Chennai"


def create_owner_context(
    database_path: str | Path,
) -> SecurityContext:
    """
    Create or authenticate the isolated automated-test
    System Owner.

    Automated tests must never depend on the local or
    production Streamlit deployment setup key.
    """

    if AuthService.owner_setup_required(
        database_path
    ):

        with (
            patch(
                "services.auth_service."
                "INITIAL_OWNER_SETUP_ENABLED",
                True,
            ),
            patch(
                "services.auth_service."
                "INITIAL_SETUP_KEY",
                TEST_SETUP_KEY,
            ),
        ):

            AuthService.bootstrap_system_owner(
                user_id=TEST_OWNER_USER_ID,
                full_name="Test System Owner",
                email=TEST_OWNER_EMAIL,
                country_location=TEST_LOCATION,
                password=TEST_PASSWORD,
                setup_key=TEST_SETUP_KEY,
                database_path=database_path,
            )

    context, _ = AuthService.authenticate(
        user_id=TEST_OWNER_USER_ID,
        password=TEST_PASSWORD,
        database_path=database_path,
    )

    return context


def create_context(
    database_path: str | Path,
    email: str,
    display_name: str = "Test User",
    *,
    user_id: str | None = None,
    role: str = USER,
    country_location: str = TEST_LOCATION,
) -> SecurityContext:
    """Provision a private user through the same admin workflow used by the UI."""
    if role == SYSTEM_OWNER:
        return create_owner_context(database_path)

    owner = create_owner_context(database_path)
    login_id = user_id or _test_user_id(email)
    try:
        UserManagementService.create_user(
            owner,
            employee_user_id=login_id,
            full_name=display_name,
            email=email,
            role=role,
            country_location=country_location,
            temporary_password=TEST_TEMPORARY_PASSWORD,
            database_path=database_path,
        )
    except ValueError as exc:
        if "already exists" not in str(exc):
            raise

    temporary_context, temporary_token = AuthService.authenticate(
        user_id=login_id,
        password=TEST_TEMPORARY_PASSWORD,
        database_path=database_path,
    )
    if temporary_context.must_change_password:
        context, _ = AuthService.complete_password_change(
            raw_token=temporary_token,
            current_password=TEST_TEMPORARY_PASSWORD,
            new_password=TEST_PASSWORD,
            database_path=database_path,
        )
        return context

    context, _ = AuthService.authenticate(
        user_id=login_id,
        password=TEST_PASSWORD,
        database_path=database_path,
    )
    return context


def _test_user_id(email: str) -> str:
    digest = hashlib.sha256(str(email).casefold().encode("utf-8")).hexdigest()[:12]
    return f"TEST-{digest.upper()}"


def build_analysis_result():
    from datetime import datetime

    from JD.jd_model import JobDescription
    from models.candidate import Candidate
    from models.match_result import MatchResult

    job = JobDescription(
        job_title="Documentation Engineer",
        company_name="Example Company",
        location="Chennai",
        experience_min=3,
        experience_max=6,
        mandatory_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        education=["Bachelor of Engineering"],
        keywords=["automotive"],
    )
    candidate = Candidate(
        full_name="Candidate One",
        email="candidate@example.com",
        phone="9999999999",
        location="Chennai",
        total_experience=5,
        education=["Bachelor of Engineering"],
        technical_skills=["Python", "SQL", "Docker"],
        source_file="candidate_one.pdf",
        raw_text="Candidate resume",
    )
    match = MatchResult(
        candidate_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        source_file=candidate.source_file,
        job_id="JD-100",
        job_title=job.job_title,
        matched_skills=["Python", "SQL"],
        matched_preferred_skills=["Docker"],
        matched_keyword_values=["automotive"],
        matched_keywords=1,
        total_keywords=1,
        required_experience=3,
        maximum_experience=6,
        candidate_experience=5,
        experience_match=True,
        education_match=True,
        skill_score=100,
        experience_score=100,
        education_score=100,
        certification_score=100,
        keyword_score=100,
        weighted_score_breakdown={"Skill": 40.0, "Experience": 25.0},
        overall_match_percentage=100,
        rank=1,
        recommendation="Highly Recommended",
        shortlisted=True,
        status="Shortlisted",
        remarks=["Strong match"],
        processed_time=datetime.now(),
    )
    return {
        "job_description": job,
        "candidates": [candidate],
        "match_results": [match],
        "errors": [],
        "summary": {
            "resumes_requested": 1,
            "resumes_processed": 1,
            "resumes_failed": 0,
        },
        "project": {
            "project_name": "Volvo Hiring",
            "client_name": "Example Company",
            "hiring_manager": "Test Manager",
            "job_id": "JD-100",
            "target_headcount": 5,
            "status": "Open",
        },
    }
