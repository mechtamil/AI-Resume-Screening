"""Screening-session configuration snapshot persistence tests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.persistence_service import PersistenceService
from tests.security_test_utils import build_analysis_result, create_context


class ConfigurationSnapshotPersistenceTests(unittest.TestCase):
    def test_session_reopens_with_immutable_configuration_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            database_path = Path(tmp) / "snapshot.db"
            user = create_context(database_path, "snapshot@example.com", "Snapshot User")
            analysis = build_analysis_result()
            analysis["configuration"] = {
                "source": "tenant_version",
                "version_id": 7,
                "version_number": 3,
                "configuration_key": "config-key-3",
                "sha256": "a" * 64,
                "file_size": 12345,
                "activated_at": "2026-07-28T10:00:00+00:00",
                "sheet_summary": {"Skills": {"Rows": 20, "Columns": 5}},
            }

            saved = PersistenceService.save_analysis_result(user, analysis, database_path)
            reopened = PersistenceService.load_session(
                user,
                saved["session_id"],
                database_path,
            )

            self.assertEqual(reopened["configuration"], analysis["configuration"])
            self.assertEqual(reopened["configuration"]["sha256"], "a" * 64)
            self.assertEqual(reopened["configuration"]["version_number"], 3)


if __name__ == "__main__":
    unittest.main()
