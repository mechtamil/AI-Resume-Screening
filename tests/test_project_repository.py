import tempfile
import unittest
from pathlib import Path

from database.project_repository import ProjectRepository
from models.recruitment_project import RecruitmentProject
from tests.security_test_utils import create_context


class ProjectRepositoryTests(unittest.TestCase):
    def test_upsert_project_uses_stable_private_project_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            context = create_context(path, "project.owner@example.com")
            repo = ProjectRepository(context, path)
            project = RecruitmentProject(
                project_name="Volvo Hiring",
                client_name="Volvo",
                job_title="Documentation Engineer",
                target_headcount=5,
            )
            first_id = repo.upsert_project(
                project,
                project_key="job:JD-100",
                job_id="JD-100",
            )
            project.target_headcount = 8
            second_id = repo.upsert_project(
                project,
                project_key="job:JD-100",
                job_id="JD-100",
            )
            self.assertEqual(first_id, second_id)
            stored = repo.get_project(first_id)
            self.assertEqual(stored["target_headcount"], 8)
            self.assertEqual(stored["tenant_id"], context.tenant_id)
            self.assertEqual(stored["owner_user_id"], context.user_id)
            self.assertEqual(len(repo.list_projects()), 1)
            repo.close()

    def test_same_project_key_is_allowed_for_different_users(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            first_context = create_context(path, "first@example.com", "First")
            second_context = create_context(path, "second@example.com", "Second")
            project = RecruitmentProject(
                project_name="Shared Name",
                job_title="Engineer",
            )

            first_repo = ProjectRepository(first_context, path)
            second_repo = ProjectRepository(second_context, path)
            first_id = first_repo.upsert_project(project, project_key="job:JD-100")
            second_id = second_repo.upsert_project(project, project_key="job:JD-100")

            self.assertNotEqual(first_id, second_id)
            self.assertEqual(len(first_repo.list_projects()), 1)
            self.assertEqual(len(second_repo.list_projects()), 1)
            self.assertIsNone(second_repo.get_project(first_id))
            first_repo.close()
            second_repo.close()


if __name__ == "__main__":
    unittest.main()
