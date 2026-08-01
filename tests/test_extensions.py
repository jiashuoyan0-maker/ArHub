from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.extension_registry import ExtensionRegistry
from backend.routers.extensions import (
    ExtensionActionRequest,
    _create_diagram,
    _create_web_project,
)


def _write_manifest(root: Path, extension_id: str, *, source: str = "builtin") -> None:
    folder = root / extension_id
    folder.mkdir(parents=True)
    payload = {
        "schema_version": "1.0",
        "id": extension_id,
        "name": f"{source} test",
        "version": "1.0.0",
        "contributes": {
            "views": [{"id": "canvas", "label": "Canvas", "kind": "diagram"}],
            "actions": [
                {"id": "create", "label": "Create", "handler": "builtin.diagram.create"}
            ],
        },
    }
    (folder / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")


class ExtensionRegistryTests(unittest.TestCase):
    def test_views_and_builtin_actions_are_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builtin = root / "builtin"
            user = root / "user"
            _write_manifest(builtin, "arhub.test")
            registry = ExtensionRegistry(builtin, user, ROOT / "extension.schema.json")

            snapshot = registry.snapshot()

            self.assertEqual(snapshot["errors"], [])
            self.assertEqual(snapshot["views"][0]["id"], "arhub.test/canvas")
            self.assertTrue(snapshot["actions"][0]["enabled"])
            self.assertEqual(snapshot["extensions"][0]["contribution_counts"]["actions"], 1)

    def test_user_manifest_action_is_discovered_but_not_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builtin = root / "builtin"
            user = root / "user"
            _write_manifest(user, "community.test", source="user")
            registry = ExtensionRegistry(builtin, user, ROOT / "extension.schema.json")

            snapshot = registry.snapshot()

            self.assertEqual(snapshot["errors"], [])
            self.assertFalse(snapshot["actions"][0]["enabled"])
            self.assertEqual(snapshot["actions"][0]["source"], "user")


class BuiltinStudioActionTests(unittest.TestCase):
    def test_diagram_action_creates_editable_source_and_svg_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            result = _create_diagram(
                workspace,
                "workflow-1",
                ExtensionActionRequest(title="Research plan", description="Review the evidence"),
            )

            source = workspace / "diagrams" / "research-plan.mmd"
            preview = source.with_suffix(".svg")
            self.assertTrue(source.is_file())
            self.assertTrue(preview.is_file())
            self.assertIn("flowchart TD", source.read_text(encoding="utf-8"))
            self.assertIn("<svg", preview.read_text(encoding="utf-8"))
            self.assertIn("arhub.diagram/preview/diagrams/research-plan.svg", result["preview_url"])

    def test_web_action_creates_a_local_previewable_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            result = _create_web_project(
                workspace,
                "workflow-2",
                ExtensionActionRequest(title="Project site", description="A concise project landing page."),
            )

            project = workspace / "web" / "project-site"
            self.assertTrue((project / "index.html").is_file())
            self.assertTrue((project / "styles.css").is_file())
            self.assertTrue((project / "app.js").is_file())
            self.assertIn("Project site", (project / "index.html").read_text(encoding="utf-8"))
            self.assertIn("arhub.web/preview/web/project-site/index.html", result["preview_url"])


if __name__ == "__main__":
    unittest.main()
