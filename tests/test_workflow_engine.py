from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services import state_store, workflow_engine
from backend.services.docx_exporter import DocxExportError


class WorkflowEngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.original_db_path = state_store.DB_PATH
        self.original_workspaces = workflow_engine.WORKSPACES_DIR
        state_store.DB_PATH = self.root / "state.db"
        workflow_engine.WORKSPACES_DIR = self.root / "workspaces"
        state_store._resume_ids.clear()
        self.events: list[dict] = []

        async def broadcast(_workflow_id: str, event: dict) -> None:
            self.events.append(event)

        workflow_engine.set_broadcast(broadcast)
        await state_store.init_db()

    async def asyncTearDown(self) -> None:
        state_store.DB_PATH = self.original_db_path
        workflow_engine.WORKSPACES_DIR = self.original_workspaces
        workflow_engine.set_broadcast(workflow_engine._noop_broadcast)
        state_store._resume_ids.clear()
        self.temp_dir.cleanup()

    async def _get(self, workflow_id: str) -> dict:
        db = await state_store.get_db()
        try:
            return await state_store.get_workflow(db, workflow_id)
        finally:
            await db.close()

    async def test_single_step_workflow_completes(self) -> None:
        workflow_id = await workflow_engine.create_new_workflow(
            "experiment_bridge", "Build an experiment", {}, False
        )
        fake_result = {
            "success": True,
            "output": "done",
            "output_files": ["experiment_results.md"],
        }
        with patch.object(
            workflow_engine.claude_runner,
            "run_skill",
            AsyncMock(return_value=fake_result),
        ):
            await workflow_engine.run_workflow(workflow_id)

        workflow = await self._get(workflow_id)
        self.assertEqual(workflow["status"], "completed")
        self.assertEqual(workflow["steps"][0]["status"], "completed")
        self.assertIn("workflow_completed", [event["type"] for event in self.events])

    async def test_docx_export_runs_as_native_workflow_step(self) -> None:
        workflow_id = await workflow_engine.create_new_workflow(
            "literature_review", "Review the literature", {}, False
        )
        workflow = await self._get(workflow_id)
        workspace = Path(workflow["workspace_dir"])
        (workspace / "LITERATURE_REVIEW.md").write_text(
            "# Literature review\n", encoding="utf-8"
        )

        async def export_docx(*_args, **_kwargs) -> dict:
            output = workspace / "LITERATURE_REVIEW.docx"
            output.write_bytes(b"docx")
            return {
                "success": True,
                "engine": "python",
                "source_path": workspace / "LITERATURE_REVIEW.md",
                "output_path": output,
                "size": output.stat().st_size,
                "log": "exported",
            }

        mock_exporter = AsyncMock(side_effect=export_docx)
        mock_runner = AsyncMock()
        with (
            patch.object(workflow_engine, "export_markdown_to_docx", mock_exporter),
            patch.object(workflow_engine.claude_runner, "run_skill", mock_runner),
        ):
            result = await workflow_engine.run_single_step(
                workflow_id, "docx-export"
            )

        mock_exporter.assert_awaited_once_with(
            workspace,
            source_file="LITERATURE_REVIEW.md",
            template="literature_review",
        )
        mock_runner.assert_not_awaited()
        workflow = await self._get(workflow_id)
        step = next(
            item for item in workflow["steps"] if item["skill_name"] == "docx-export"
        )
        self.assertEqual(step["status"], "completed")
        self.assertEqual(step["output_files"], ["LITERATURE_REVIEW.docx"])
        self.assertEqual(result["output_files"], ["LITERATURE_REVIEW.docx"])
        self.assertIn("step_completed", [event["type"] for event in self.events])

    async def test_docx_export_failure_marks_step_and_workflow_failed(self) -> None:
        workflow_id = await workflow_engine.create_new_workflow(
            "literature_review", "Review the literature", {}, False
        )
        workflow = await self._get(workflow_id)
        workspace = Path(workflow["workspace_dir"])
        (workspace / "LITERATURE_REVIEW.md").write_text(
            "# Literature review\n", encoding="utf-8"
        )

        mock_exporter = AsyncMock(
            side_effect=DocxExportError("converter unavailable")
        )
        mock_runner = AsyncMock()
        with (
            patch.object(workflow_engine, "export_markdown_to_docx", mock_exporter),
            patch.object(workflow_engine.claude_runner, "run_skill", mock_runner),
            self.assertRaisesRegex(RuntimeError, "converter unavailable"),
        ):
            await workflow_engine.run_single_step(workflow_id, "docx-export")

        mock_runner.assert_not_awaited()
        workflow = await self._get(workflow_id)
        step = next(
            item for item in workflow["steps"] if item["skill_name"] == "docx-export"
        )
        self.assertEqual(workflow["status"], "failed")
        self.assertEqual(step["status"], "failed")
        self.assertIn("converter unavailable", step["error_message"])
        self.assertIn("step_failed", [event["type"] for event in self.events])

    async def test_checkpoint_approve_and_feedback_are_persistent(self) -> None:
        workflow_id = await workflow_engine.create_new_workflow(
            "paper_writing", "Draft a paper", {}, True
        )
        fake_result = {"success": True, "output": "done", "output_files": []}
        mock_runner = AsyncMock(return_value=fake_result)
        with patch.object(workflow_engine.claude_runner, "run_skill", mock_runner):
            await workflow_engine.run_workflow(workflow_id)
            workflow = await self._get(workflow_id)
            self.assertEqual(workflow["status"], "paused")
            self.assertEqual(workflow["steps"][0]["status"], "waiting_checkpoint")

            result = await workflow_engine.resolve_checkpoint(
                workflow_id, {"action": "feedback", "data": {"feedback": "Add evidence"}}
            )
            self.assertTrue(result["resume"])
            workflow = await self._get(workflow_id)
            self.assertEqual(workflow["steps"][0]["status"], "pending")
            self.assertEqual(
                workflow["params"]["_checkpoint_feedback"]["paper-plan"],
                "Add evidence",
            )

            await workflow_engine.run_workflow(workflow_id)
            await workflow_engine.resolve_checkpoint(
                workflow_id, {"action": "approve", "data": {}}
            )
            await workflow_engine.run_workflow(workflow_id)

        workflow = await self._get(workflow_id)
        self.assertEqual(workflow["steps"][0]["status"], "completed")
        self.assertEqual(workflow["steps"][1]["status"], "waiting_checkpoint")
        self.assertGreaterEqual(mock_runner.await_count, 3)


if __name__ == "__main__":
    unittest.main()
