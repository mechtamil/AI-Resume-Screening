"""End-to-end authorization tests for explicit RecruitOS sharing."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from database.database import Database
from services.authorization_service import READER
from services.persistence_service import PersistenceService
from services.sharing_service import SharingService
from tests.security_test_utils import build_analysis_result, create_context


class SharingServiceTests(unittest.TestCase):
    def test_project_is_private_until_explicitly_shared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sharing.db"
            owner = create_context(path, "share.owner@example.com", "Share Owner")
            recipient = create_context(
                path,
                "share.reader@example.com",
                "Share Reader",
                role=READER,
            )
            intruder = create_context(
                path,
                "share.intruder@example.com",
                "Unassigned Reader",
                role=READER,
            )
            saved = PersistenceService.save_analysis_result(
                owner,
                build_analysis_result(),
                path,
            )

            self.assertEqual(SharingService.list_received_shares(recipient, path), [])
            with self.assertRaisesRegex(LookupError, "not available"):
                PersistenceService.load_session(recipient, saved["session_id"], path)

            share = SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=recipient.user_id,
                access_role=SharingService.ACCESS_READER,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                note="Read-only hiring review",
                database_path=path,
            )
            self.assertEqual(share["access_role"], "READER")
            self.assertEqual(share["status"], "ACTIVE")

            received = SharingService.list_received_shares(recipient, path)
            self.assertEqual(len(received), 1)
            self.assertEqual(received[0]["project_id"], saved["project_id"])

            sessions = SharingService.list_shared_sessions(
                recipient,
                int(share["id"]),
                path,
            )
            self.assertEqual([item["id"] for item in sessions], [saved["session_id"]])

            result = SharingService.load_shared_session(
                recipient,
                share_id=int(share["id"]),
                session_id=saved["session_id"],
                database_path=path,
            )
            self.assertTrue(result["persistence"]["shared_read_only"])
            self.assertTrue(result["sharing"]["read_only"])
            self.assertEqual(result["storage"], {})
            self.assertEqual(result["candidates"][0].raw_text, "")
            self.assertEqual(result["match_results"][0].rank, 1)

            with self.assertRaisesRegex(PermissionError, "not available"):
                SharingService.load_shared_session(
                    intruder,
                    share_id=int(share["id"]),
                    session_id=saved["session_id"],
                    database_path=path,
                )

            # Explicit sharing does not weaken the owner-only persistence API.
            with self.assertRaisesRegex(LookupError, "not available"):
                PersistenceService.load_session(recipient, saved["session_id"], path)

    def test_duplicate_active_assignment_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.db"
            owner = create_context(path, "duplicate.owner@example.com", "Owner")
            reader = create_context(path, "duplicate.reader@example.com", "Reader", role=READER)
            saved = PersistenceService.save_analysis_result(owner, build_analysis_result(), path)
            SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=reader.user_id,
                access_role=SharingService.ACCESS_READER,
                database_path=path,
            )
            with self.assertRaisesRegex(ValueError, "active share already exists"):
                SharingService.grant_project_share(
                    owner,
                    project_id=saved["project_id"],
                    grantee_user_id=reader.user_id,
                    access_role=SharingService.ACCESS_REVIEWER,
                    database_path=path,
                )

    def test_reviewer_progress_does_not_modify_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.db"
            owner = create_context(path, "review.owner@example.com", "Review Owner")
            reviewer = create_context(
                path,
                "review.reader@example.com",
                "Assigned Reviewer",
                role=READER,
            )
            saved = PersistenceService.save_analysis_result(
                owner,
                build_analysis_result(),
                path,
            )
            share = SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=reviewer.user_id,
                access_role=SharingService.ACCESS_REVIEWER,
                database_path=path,
            )
            self.assertEqual(share["review_status"], "ASSIGNED")

            updated = SharingService.update_review(
                reviewer,
                share_id=int(share["id"]),
                review_status=SharingService.REVIEW_COMPLETED,
                review_note="Evidence reviewed; shortlist is supported.",
                database_path=path,
            )
            self.assertEqual(updated["review_status"], "COMPLETED")
            self.assertTrue(updated["reviewed_at"])
            self.assertIn("shortlist", updated["review_note"])

            reopened = PersistenceService.load_session(owner, saved["session_id"], path)
            self.assertEqual(reopened["match_results"][0].overall_match_percentage, 100)
            self.assertEqual(reopened["match_results"][0].remarks, ["Strong match"])

    def test_reader_cannot_update_reviewer_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reader.db"
            owner = create_context(path, "reader.owner@example.com", "Owner")
            reader = create_context(path, "reader.target@example.com", "Reader", role=READER)
            saved = PersistenceService.save_analysis_result(owner, build_analysis_result(), path)
            share = SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=reader.user_id,
                access_role=SharingService.ACCESS_READER,
                database_path=path,
            )
            with self.assertRaisesRegex(PermissionError, "Reader access"):
                SharingService.update_review(
                    reader,
                    share_id=int(share["id"]),
                    review_status=SharingService.REVIEW_COMPLETED,
                    database_path=path,
                )

    def test_revocation_removes_access_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "revoke.db"
            owner = create_context(path, "revoke.owner@example.com", "Owner")
            reader = create_context(path, "revoke.reader@example.com", "Reader", role=READER)
            saved = PersistenceService.save_analysis_result(owner, build_analysis_result(), path)
            share = SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=reader.user_id,
                access_role=SharingService.ACCESS_READER,
                database_path=path,
            )

            self.assertTrue(SharingService.revoke_share(owner, int(share["id"]), path))
            self.assertEqual(SharingService.list_received_shares(reader, path), [])
            with self.assertRaisesRegex(PermissionError, "not available"):
                SharingService.load_shared_session(
                    reader,
                    share_id=int(share["id"]),
                    session_id=saved["session_id"],
                    database_path=path,
                )
            with self.assertRaisesRegex(PermissionError, "not permitted"):
                SharingService.revoke_share(reader, int(share["id"]), path)

    def test_expired_share_is_closed_and_audited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expiry.db"
            owner = create_context(path, "expiry.owner@example.com", "Owner")
            reader = create_context(path, "expiry.reader@example.com", "Reader", role=READER)
            saved = PersistenceService.save_analysis_result(owner, build_analysis_result(), path)
            share = SharingService.grant_project_share(
                owner,
                project_id=saved["project_id"],
                grantee_user_id=reader.user_id,
                access_role=SharingService.ACCESS_READER,
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                database_path=path,
            )

            with Database(path) as database:
                database.create_tables()
                database.connection.execute(
                    "UPDATE record_shares SET expires_at = ? WHERE id = ?",
                    (
                        (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(
                            timespec="seconds"
                        ),
                        int(share["id"]),
                    ),
                )
                database.connection.commit()

            self.assertEqual(SharingService.list_received_shares(reader, path), [])
            owned = SharingService.list_owned_shares(
                owner,
                project_id=saved["project_id"],
                database_path=path,
            )
            self.assertEqual(owned[0]["status"], "EXPIRED")
            actions = {
                item["action"]
                for item in SharingService.list_share_audit(owner, int(share["id"]), path)
            }
            self.assertIn("share.granted", actions)
            self.assertIn("share.expired", actions)

    def test_non_owner_and_cross_location_sharing_are_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "denial.db"
            owner = create_context(path, "deny.owner@example.com", "Owner")
            other = create_context(path, "deny.other@example.com", "Other")
            same_location_reader = create_context(
                path,
                "deny.local@example.com",
                "Local Reader",
                role=READER,
            )
            remote = create_context(
                path,
                "deny.remote@example.com",
                "Remote Reader",
                role=READER,
                country_location="France - Paris",
            )
            saved = PersistenceService.save_analysis_result(owner, build_analysis_result(), path)

            with self.assertRaisesRegex(PermissionError, "project owner"):
                SharingService.grant_project_share(
                    other,
                    project_id=saved["project_id"],
                    grantee_user_id=same_location_reader.user_id,
                    access_role=SharingService.ACCESS_READER,
                    database_path=path,
                )

            with self.assertRaisesRegex(PermissionError, "country/location"):
                SharingService.grant_project_share(
                    owner,
                    project_id=saved["project_id"],
                    grantee_user_id=remote.user_id,
                    access_role=SharingService.ACCESS_READER,
                    database_path=path,
                )

    def test_recipient_cannot_open_session_from_another_shared_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-boundary.db"
            owner = create_context(path, "session.owner@example.com", "Owner")
            reader = create_context(path, "session.reader@example.com", "Reader", role=READER)
            first_result = build_analysis_result()
            first_result["project"]["job_id"] = "SHARE-A"
            first = PersistenceService.save_analysis_result(owner, first_result, path)
            second_result = build_analysis_result()
            second_result["project"]["job_id"] = "SHARE-B"
            second = PersistenceService.save_analysis_result(owner, second_result, path)
            share = SharingService.grant_project_share(
                owner,
                project_id=first["project_id"],
                grantee_user_id=reader.user_id,
                access_role=SharingService.ACCESS_READER,
                database_path=path,
            )
            with self.assertRaisesRegex(PermissionError, "outside this share"):
                SharingService.load_shared_session(
                    reader,
                    share_id=int(share["id"]),
                    session_id=second["session_id"],
                    database_path=path,
                )


if __name__ == "__main__":
    unittest.main()
