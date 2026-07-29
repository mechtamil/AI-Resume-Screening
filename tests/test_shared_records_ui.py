"""Static UI contracts for explicit sharing and read-only evidence."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class SharedRecordsUiTests(unittest.TestCase):
    def test_app_routes_shared_records_to_real_workspace(self) -> None:
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("from ui.shared_records import show_shared_records", source)
        self.assertIn("show_shared_records(security_context)", source)
        self.assertNotIn("Controlled sharing is delivered in Sprint 5.7.1D", source)

    def test_candidate_database_exposes_owner_share_controls(self) -> None:
        source = (ROOT / "ui" / "candidate_database.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Share project and assign review", source)
        self.assertIn("Grant Project Access", source)
        self.assertIn("Revoke Selected Access", source)
        self.assertIn("SharingService.grant_project_share", source)
        self.assertIn("SharingService.revoke_share", source)

    def test_shared_workspace_is_read_only_evidence_view(self) -> None:
        source = (ROOT / "ui" / "shared_records.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Open Read-Only Evidence", source)
        self.assertIn("Editing, deletion", source)
        self.assertIn("SharingService.load_shared_session", source)
        self.assertNotIn("st.download_button", source)
        self.assertNotIn("delete_project", source)
        self.assertNotIn("SecureExportService", source)

    def test_reviewer_progress_is_separate_from_evidence(self) -> None:
        source = (ROOT / "ui" / "shared_records.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Update Review Progress", source)
        self.assertIn("does not alter candidate evidence", source)
        self.assertIn("SharingService.update_review", source)


if __name__ == "__main__":
    unittest.main()
