from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.routers import artifacts


class ArtifactWorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_workspace_must_stay_under_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "workspaces"
            root.mkdir()
            valid = root / "wf-valid"
            outside = base / "outside"
            db = AsyncMock()

            with (
                patch.object(artifacts, "WORKSPACES_DIR", root),
                patch.object(artifacts, "get_db", AsyncMock(return_value=db)),
                patch.object(
                    artifacts,
                    "get_workflow",
                    AsyncMock(return_value={"workspace_dir": str(valid)}),
                ),
            ):
                self.assertEqual(await artifacts._workspace("wf-valid"), valid.resolve())
            self.assertTrue(valid.is_dir())

            with (
                patch.object(artifacts, "WORKSPACES_DIR", root),
                patch.object(artifacts, "get_db", AsyncMock(return_value=db)),
                patch.object(
                    artifacts,
                    "get_workflow",
                    AsyncMock(return_value={"workspace_dir": str(outside)}),
                ),
            ):
                with self.assertRaises(HTTPException) as caught:
                    await artifacts._workspace("wf-outside")

            self.assertEqual(caught.exception.status_code, 400)
            self.assertFalse(outside.exists())

    async def test_stale_workspace_is_migrated_to_current_data_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "workspaces"
            migrated = root / "wf-migrated"
            migrated.mkdir(parents=True)
            db = AsyncMock()
            update = AsyncMock()

            with (
                patch.object(artifacts, "WORKSPACES_DIR", root),
                patch.object(artifacts, "get_db", AsyncMock(return_value=db)),
                patch.object(
                    artifacts,
                    "get_workflow",
                    AsyncMock(return_value={"workspace_dir": str(base / "retired")}),
                ),
                patch.object(artifacts, "update_workflow", update),
            ):
                result = await artifacts._workspace("wf-migrated")

            self.assertEqual(result, migrated.resolve())
            update.assert_awaited_once_with(
                db, "wf-migrated", workspace_dir=str(migrated.resolve())
            )
            db.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
