from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import HTTPException

from backend.routers import editor
from backend.services import editor_ai
from backend.services.editor_agent import EditorAgentManager, build_diffs


class FakeRunner:
    def __init__(self, *, success: bool = True) -> None:
        self.success = success
        self.cancelled: list[str] = []

    async def run_skill(self, _skill: str, _arguments: str, cwd: str | Path, *_args, **kwargs):
        path = Path(cwd) / "paper" / "main.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Revised\n", encoding="utf-8")
        callback = kwargs.get("on_output")
        if callback:
            await callback("Updated paper/main.md")
        return {
            "success": self.success,
            "output": "Revision complete" if self.success else "Revision interrupted",
            "output_files": ["paper/main.md"],
        }

    def cancel(self, workflow_id: str) -> bool:
        self.cancelled.append(workflow_id)
        return True


class EditorAiTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_single_file_response_is_normalized(self) -> None:
        response = {
            "summary": "Updated title",
            "target_file": "paper/main.md",
            "modified_content": "# New title\n",
        }
        with patch.object(
            editor_ai,
            "call_llm",
            AsyncMock(return_value="```json\n" + json.dumps(response) + "\n```"),
        ):
            result = await editor_ai.ai_edit(
                "Change the title",
                "paper/main.md",
                "# Old title\n",
                ["paper/main.md"],
                role="markdown",
            )
        self.assertEqual(result["target_file"], "paper/main.md")
        self.assertEqual(result["modified_content"], "# New title\n")
        self.assertEqual(result["summary"], "Updated title")


class EditorAgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_agent_change_is_applied_and_undoable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            source = workspace / "paper" / "main.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Original\n", encoding="utf-8")
            manager = EditorAgentManager(FakeRunner(), root / "state")

            run = await manager.start(
                "wf-test",
                workspace,
                "Revise the title",
                mode="markdown",
                current_file="paper/main.md",
            )
            self.assertIsNotNone(run.task)
            await run.task

            self.assertEqual(source.read_text(encoding="utf-8"), "# Revised\n")
            status = manager.check("wf-test", workspace)
            self.assertFalse(status["running"])
            self.assertEqual(status["diffs"], [])
            self.assertTrue(status["can_undo"])
            self.assertEqual(status["applied_files"], ["paper/main.md"])

            result = manager.undo("wf-test", workspace)
            self.assertEqual(result["restored"], ["paper/main.md"])
            self.assertEqual(source.read_text(encoding="utf-8"), "# Original\n")
            self.assertFalse(manager.check("wf-test", workspace)["can_undo"])

    async def test_failed_agent_keeps_reviewable_diff_until_apply(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            source = workspace / "paper" / "main.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Original\n", encoding="utf-8")
            manager = EditorAgentManager(FakeRunner(success=False), root / "state")

            run = await manager.start(
                "wf-test", workspace, "Revise the title", mode="markdown"
            )
            await run.task
            status = manager.check("wf-test", workspace)
            self.assertEqual(source.read_text(encoding="utf-8"), "# Original\n")
            self.assertEqual([item["path"] for item in status["diffs"]], ["paper/main.md"])

            applied = manager.apply("wf-test", workspace, ["paper/main.md"])
            self.assertEqual(applied["applied"], ["paper/main.md"])
            self.assertEqual(source.read_text(encoding="utf-8"), "# Revised\n")

    def test_missing_sandbox_has_no_pending_diff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            (workspace / "keep.txt").write_text("keep", encoding="utf-8")
            self.assertEqual(build_diffs(workspace, Path(directory) / "missing"), [])


class EditorRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name) / "workspace"
        self.workspace.mkdir()
        self.workflow = {
            "id": "wf-test",
            "template": "paper_writing",
            "params": {},
            "workspace_dir": str(self.workspace),
        }
        self.workspace_patch = patch.object(
            editor,
            "_workspace_and_workflow",
            AsyncMock(return_value=(self.workspace, self.workflow)),
        )
        self.workspace_patch.start()

    async def asyncTearDown(self) -> None:
        self.workspace_patch.stop()
        self.temp_dir.cleanup()

    async def test_file_round_trip_and_tree_contract(self) -> None:
        created = await editor.create_file(
            "wf-test", editor.CreateFileRequest(path="paper/main.tex", content="Hello")
        )
        self.assertEqual(created["path"], "paper/main.tex")
        loaded = await editor.read_file("wf-test", "paper/main.tex")
        self.assertEqual(loaded, {"content": "Hello"})

        await editor.save_file(
            "wf-test", editor.SaveRequest(path="paper/main.tex", content="Revised")
        )
        files = await editor.list_files("wf-test")
        self.assertEqual(files[0]["name"], "main.tex")
        self.assertEqual(files[0]["dir"], "paper")
        self.assertEqual(files[0]["type"], "tex")

    async def test_workspace_escape_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await editor.save_file(
                "wf-test", editor.SaveRequest(path="../outside.txt", content="blocked")
            )
        self.assertEqual(caught.exception.status_code, 400)

    async def test_mode_and_stats_match_frontend_shape(self) -> None:
        paper = self.workspace / "paper"
        paper.mkdir()
        (paper / "main.tex").write_text("中文 text words", encoding="utf-8")
        mode = await editor.get_mode("wf-test")
        stats = await editor.get_stats("wf-test")
        self.assertEqual(mode, {"mode": "latex", "main_file": "paper/main.tex"})
        self.assertIn("total_words", stats)
        self.assertIn("pdf_pages", stats)
        self.assertEqual(stats["total_words"]["chinese"], 2)

    def test_frontend_route_surface_is_complete(self) -> None:
        routes = {
            (method, route.path)
            for route in editor.router.routes
            for method in route.methods
        }
        expected = {
            ("GET", "/api/editor/{wf_id}/mode"),
            ("GET", "/api/editor/{wf_id}/files"),
            ("GET", "/api/editor/{wf_id}/file"),
            ("PUT", "/api/editor/{wf_id}/file"),
            ("POST", "/api/editor/{wf_id}/ai-agent"),
            ("GET", "/api/editor/{wf_id}/ai-agent-check"),
            ("POST", "/api/editor/{wf_id}/run-script"),
            ("POST", "/api/editor/{wf_id}/compile"),
            ("GET", "/api/editor/{wf_id}/chat-history"),
            ("DELETE", "/api/editor/{wf_id}/chat-history"),
        }
        self.assertTrue(expected.issubset(routes))


if __name__ == "__main__":
    unittest.main()
