# ============================================================
# RecruitOS - AI Resume Screening & Recruitment Platform
# Master Project Specification
# ============================================================

# PROJECT INFORMATION

Project Name: RecruitOS

Project Type:
Enterprise AI Recruitment Platform

Project Owner:
Tamilvanan A

Lead Software Architect:
ChatGPT

Primary Technology Stack:
- Python 3.x
- Streamlit
- Pandas
- OpenPyXL
- SQLite
- PDFPlumber
- python-docx
- Regex
- Logging
- Git

Project Status:
🟢 Active Development

Repository:
GitHub Repository URL

Default Branch:
main

Project Start Date:

Current Version:

Current Release:

Last Updated:

---

# PROJECT OBJECTIVE

Build an enterprise-grade AI Recruitment Platform capable of:

- Resume Parsing
- Job Description Parsing
- Skill Extraction
- Candidate Matching
- Candidate Ranking
- AI Recommendation Engine
- Interview Shortlisting
- Dashboard
- Reports
- Authentication
- Database
- Audit Logs
- Production Deployment

---

# CURRENT PROJECT STATE

RecruitOS Version:

Release:

Sprint:

Milestone:

Application Status:

✅ Running
⚠ Partially Working
❌ Broken

Current Branch:

Last Git Commit:

---

# COMPLETED SPRINTS

Sprint 1
Status:
Completed

Milestones:
-
-

Major Deliverables:
-
-

---

Sprint 2

Status:

Completed

Milestones:
-
-

Major Deliverables:
-
-

---

Sprint 3

Status:

Completed

Milestones:
-
-

Major Deliverables:
-
-

---

Sprint 4

Status:

Completed

Milestones:
-
-

Major Deliverables:
-
-

---

Current Sprint

Sprint:

Milestone:

Progress:

---

# COMPLETED MODULES

Core

✔ App Entry
✔ Configuration
✔ Folder Structure

Parsers

✔ PDF Parser
✔ DOCX Parser
✔ TXT Parser

Models

✔ Resume Model
✔ JD Model

Services

✔ Document Manager
✔ Extraction Service
✔ Processing Service

UI

✔ Home
✔ Resume Upload
✔ JD Upload
✔ Results

Testing

✔ Parser Tests
✔ Processing Tests
✔ Results Tests

Git

✔ Repository
✔ Branch
✔ Commit Workflow

---

# MODULES IN PROGRESS

-

-

-

---

# PLANNED MODULES

Matching Engine

Scoring Engine

Ranking Engine

Recommendation Engine

Dashboard

Analytics

Authentication

Database Integration

Admin Panel

Export Engine

Deployment

---

# CURRENT ARCHITECTURE

RecruitOS

app.py

config/

parser/

services/

models/

database/

ui/

utils/

reports/

tests/

assets/

Resume/

JD/

Skill_List/

---

# ARCHITECTURE DECISIONS

Use Service Layer Architecture

Keep Models independent

Keep Parsing isolated

Keep UI independent

Business Logic belongs only in Services

Use dependency flow:

UI
↓

Services
↓

Models
↓

Utilities

---

# CODING STANDARDS

Python PEP8

Type Hints

Docstrings

Logging

Exception Handling

No Hardcoded Paths

Modular Design

Reusable Components

---

# PROJECT CONVENTIONS

Naming

snake_case

PascalCase for classes

UPPER_CASE for constants

Directory Rules

One responsibility per module

Avoid duplicate logic

Reusable services

---

# TESTING STATUS

Parser Tests

Status:

Extraction Tests

Status:

Processing Tests

Status:

UI Tests

Status:

Integration Tests

Status:

---

# KNOWN ISSUES

-

-

-

---

# TECHNICAL DEBT

-

-

-

---

# CHANGELOG SUMMARY

Version

Changes

Date

---

# OUTSTANDING TASKS

High Priority

-

-

Medium Priority

-

-

Low Priority

-

-

---

# NEXT PLANNED MILESTONE

Sprint:

Milestone:

Objective:

Files Expected to Change:

-

-

-

Expected Deliverables:

-

-

---

# DEVELOPMENT WORKFLOW

For every development cycle:

1.
Review PROJECT_SPEC.md

2.
Review ROADMAP.md

3.
Review ARCHITECTURE.md

4.
Review VERSION

5.
Review TODO

6.
Review CHANGELOG

7.
Review current source code

8.
Determine next milestone

9.
Generate complete code

10.
Generate tests

11.
Generate Git commands

12.
Update PROJECT_SPEC.md

---

# DEFINITION OF DONE

Every milestone is considered complete only if:

✔ Code Compiles

✔ Tests Pass

✔ Streamlit Runs

✔ Git Commit Completed

✔ Documentation Updated

✔ PROJECT_SPEC Updated

✔ CHANGELOG Updated

✔ VERSION Updated

✔ Ready for Next Sprint

---

# NOTES

This document is the single source of truth for RecruitOS.

Every future development session must begin by reviewing this file before writing any code.