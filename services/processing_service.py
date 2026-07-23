"""
============================================================
RecruitOS
Processing Service
Version : 1.0
Author  : Tamilvanan A

Description:
Coordinates the complete resume screening workflow.

Flow:
JD -> Read -> Parse
Resume -> Read -> Parse
Return structured objects
============================================================
"""

from typing import List, Dict

from services.document_manager import DocumentManager

from JD.jd_parser import JDParser

from parser.resume_parser import ResumeParser


class ProcessingService:

    @staticmethod
    def process_documents(
        jd_path: str,
        resume_paths: List[str]
    ) -> Dict:

        # ----------------------------
        # Process JD
        # ----------------------------

        jd_document = DocumentManager.read_document(jd_path)

        jd = JDParser.parse(jd_document)

        # ----------------------------
        # Process Resumes
        # ----------------------------

        candidates = []

        for resume in resume_paths:

            resume_document = DocumentManager.read_document(
                resume
            )

            candidate = ResumeParser.parse(
                resume_document
            )

            candidates.append(candidate)

        return {

            "job_description": jd,

            "candidates": candidates

        }