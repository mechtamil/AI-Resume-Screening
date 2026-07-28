"""Pure tests for RecruitOS guided workflow navigation decisions."""
from __future__ import annotations

import unittest

from ui.navigation import workflow_neighbors


class NavigationTests(unittest.TestCase):
    def test_results_are_not_next_until_analysis_exists(self):
        allowed = ["Home", "Resume Screening", "Results", "Candidate Database"]
        previous_page, next_page = workflow_neighbors(
            "Resume Screening",
            allowed,
            has_results=False,
        )
        self.assertEqual(previous_page, "Home")
        self.assertIsNone(next_page)

    def test_results_and_database_link_when_analysis_exists(self):
        allowed = ["Home", "Resume Screening", "Results", "Candidate Database"]
        self.assertEqual(
            workflow_neighbors("Resume Screening", allowed, has_results=True),
            ("Home", "Results"),
        )
        self.assertEqual(
            workflow_neighbors("Results", allowed, has_results=True),
            ("Resume Screening", "Candidate Database"),
        )

    def test_non_workflow_page_can_return_home(self):
        self.assertEqual(
            workflow_neighbors("Administration", ["Home", "Administration"], has_results=False),
            (None, "Home"),
        )


if __name__ == "__main__":
    unittest.main()
