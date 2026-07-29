from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models.schemas import StepInfo, WorkflowCreate, WorkflowInfo
from backend.services import state_store


class StateStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = state_store.DB_PATH
        state_store.DB_PATH = Path(self.temp_dir.name) / "state.db"
        state_store._resume_ids.clear()
        await state_store.init_db()

    async def asyncTearDown(self) -> None:
        state_store.DB_PATH = self.original_db_path
        state_store._resume_ids.clear()
        self.temp_dir.cleanup()

    async def test_settings_round_trip(self) -> None:
        await state_store.save_settings(
            {
                "executor_base_url": "https://example.test/v1",
                "executor_model_id": "test-model",
            }
        )

        self.assertEqual(
            await state_store.get_setting("executor_model_id"), "test-model"
        )
        self.assertEqual(await state_store.get_setting("missing", "fallback"), "fallback")
        settings = await state_store.get_all_settings()
        self.assertEqual(settings["executor_base_url"], "https://example.test/v1")

    async def test_workflow_round_trip_update_export_and_import(self) -> None:
        workflow = {
            "id": "wf-source",
            "template": "paper_writing",
            "title": "Open source runtime",
            "params": {"language": "zh"},
            "enable_checkpoints": True,
            "workspace_dir": str(Path(self.temp_dir.name) / "wf-source"),
            "steps": [
                {
                    "skill_name": "paper-plan",
                    "display_name": "Paper plan",
                    "step_order": 0,
                    "has_checkpoint": True,
                    "checkpoint_type": "approve",
                    "output_files": ["PAPER_PLAN.md"],
                    "primary_output": "PAPER_PLAN.md",
                }
            ],
        }

        db = await state_store.get_db()
        try:
            await state_store.create_workflow(db, workflow)
            loaded = await state_store.get_workflow(db, "wf-source")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["params"], {"language": "zh"})
            self.assertTrue(loaded["enable_checkpoints"])
            self.assertEqual(loaded["steps"][0]["output_files"], ["PAPER_PLAN.md"])

            await state_store.update_workflow(
                db, "wf-source", status="running", current_step="paper-plan"
            )
            loaded = await state_store.get_workflow(db, "wf-source")
            self.assertEqual(loaded["status"], "running")
        finally:
            await db.close()

        await state_store.append_log(
            "wf-source", "step started", step_name="paper-plan", level="progress"
        )
        exported = await state_store.export_workflow_data("wf-source")
        self.assertIsNotNone(exported)
        self.assertEqual(exported["logs"][0]["message"], "step started")

        await state_store.import_workflow_data(
            exported,
            "wf-imported",
            str(Path(self.temp_dir.name) / "wf-imported"),
        )
        db = await state_store.get_db()
        try:
            imported = await state_store.get_workflow(db, "wf-imported")
            self.assertEqual(imported["status"], "pending")
            self.assertEqual(imported["steps"][0]["workflow_id"], "wf-imported")
        finally:
            await db.close()

        await state_store.init_db()
        self.assertEqual(state_store.get_workflows_to_resume(), ["wf-source"])
        self.assertEqual(state_store.get_workflows_to_resume(), [])


class SchemaTests(unittest.TestCase):
    def test_models_validate_public_contract(self) -> None:
        create = WorkflowCreate(template="paper_writing", title="A task")
        info = WorkflowInfo(
            id="wf-1",
            template=create.template,
            title=create.title,
            steps=[
                StepInfo(
                    skill_name="paper-plan",
                    display_name="Paper plan",
                    step_order=0,
                )
            ],
        )
        self.assertEqual(info.steps[0].status.value, "pending")


if __name__ == "__main__":
    unittest.main()
