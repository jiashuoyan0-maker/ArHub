"""SQLite persistence for settings, workflows, steps, logs and checkpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiosqlite

try:
    from config import BACKEND_DIR, DB_PATH as CONFIG_DB_PATH
except ModuleNotFoundError:  # Package import used by tests and library consumers.
    from backend.config import BACKEND_DIR, DB_PATH as CONFIG_DB_PATH

log = logging.getLogger(__name__)

DB_PATH = Path(CONFIG_DB_PATH)
SCHEMA_PATH = BACKEND_DIR / "db" / "schema.sql"

_JSON_FIELDS = {"params", "output_files", "data", "response"}
_WORKFLOW_FIELDS = {
    "template",
    "title",
    "params",
    "status",
    "current_step",
    "workspace_dir",
    "enable_checkpoints",
}
_STEP_FIELDS = {
    "display_name",
    "step_order",
    "status",
    "has_checkpoint",
    "checkpoint_type",
    "output_files",
    "primary_output",
    "started_at",
    "completed_at",
    "error_message",
}
_resume_ids: list[str] = []


def _json_load(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _encode_value(name: str, value: Any) -> Any:
    if name in _JSON_FIELDS:
        return json.dumps(value, ensure_ascii=False)
    if name in {"enable_checkpoints", "has_checkpoint"}:
        return int(bool(value))
    return value


def _workflow_from_row(row: aiosqlite.Row) -> dict[str, Any]:
    data = dict(row)
    data["params"] = _json_load(data.get("params"), {})
    data["enable_checkpoints"] = bool(data.get("enable_checkpoints"))
    return data


def _step_from_row(row: aiosqlite.Row) -> dict[str, Any]:
    data = dict(row)
    data["output_files"] = _json_load(data.get("output_files"), [])
    data["has_checkpoint"] = bool(data.get("has_checkpoint"))
    return data


async def get_db() -> aiosqlite.Connection:
    """Open a configured database connection with dictionary-like rows."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH, timeout=30)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 30000")
    return db


async def _ensure_columns(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(workflow_steps)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "primary_output" not in columns:
        await db.execute("ALTER TABLE workflow_steps ADD COLUMN primary_output TEXT")


async def init_db() -> None:
    """Create or migrate the database and remember interrupted workflow IDs."""
    if not SCHEMA_PATH.is_file():
        raise RuntimeError(f"Database schema is missing: {SCHEMA_PATH}")

    db = await get_db()
    try:
        await db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        await _ensure_columns(db)
        cursor = await db.execute(
            "SELECT id FROM workflows WHERE status = 'running' ORDER BY updated_at"
        )
        _resume_ids[:] = [row[0] for row in await cursor.fetchall()]
        await db.commit()
    finally:
        await db.close()


def get_workflows_to_resume() -> list[str]:
    """Return interrupted workflow IDs once after backend startup."""
    result = list(_resume_ids)
    _resume_ids.clear()
    return result


async def create_workflow(db: aiosqlite.Connection, wf: dict[str, Any]) -> None:
    """Insert a workflow and its ordered step definitions atomically."""
    await db.execute(
        """
        INSERT INTO workflows
            (id, template, title, params, status, current_step, workspace_dir,
             enable_checkpoints, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE(?, CURRENT_TIMESTAMP), COALESCE(?, CURRENT_TIMESTAMP))
        """,
        (
            wf["id"],
            wf["template"],
            wf["title"],
            _encode_value("params", wf.get("params", {})),
            wf.get("status", "pending"),
            wf.get("current_step"),
            wf.get("workspace_dir"),
            _encode_value("enable_checkpoints", wf.get("enable_checkpoints", False)),
            wf.get("created_at"),
            wf.get("updated_at"),
        ),
    )

    for order, step in enumerate(wf.get("steps", [])):
        await db.execute(
            """
            INSERT INTO workflow_steps
                (workflow_id, skill_name, display_name, step_order, status,
                 has_checkpoint, checkpoint_type, output_files, primary_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wf["id"],
                step["skill_name"],
                step.get("display_name", step["skill_name"]),
                step.get("step_order", order),
                step.get("status", "pending"),
                _encode_value("has_checkpoint", step.get("has_checkpoint", False)),
                step.get("checkpoint_type"),
                _encode_value("output_files", step.get("output_files", [])),
                step.get("primary_output"),
            ),
        )
    await db.commit()


async def get_workflow(
    db: aiosqlite.Connection, wf_id: str
) -> dict[str, Any] | None:
    cursor = await db.execute("SELECT * FROM workflows WHERE id = ?", (wf_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    workflow = _workflow_from_row(row)
    cursor = await db.execute(
        "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_order, id",
        (wf_id,),
    )
    workflow["steps"] = [_step_from_row(item) for item in await cursor.fetchall()]
    return workflow


async def list_workflows(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    cursor = await db.execute("SELECT * FROM workflows ORDER BY created_at DESC")
    return [_workflow_from_row(row) for row in await cursor.fetchall()]


async def update_workflow(
    db: aiosqlite.Connection, wf_id: str, **fields: Any
) -> None:
    updates = {key: value for key, value in fields.items() if key in _WORKFLOW_FIELDS}
    if not updates:
        return
    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = [_encode_value(key, value) for key, value in updates.items()]
    values.append(wf_id)

    for attempt in range(5):
        try:
            await db.execute(
                f"UPDATE workflows SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )
            await db.commit()
            return
        except aiosqlite.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt == 4:
                raise
            await asyncio.sleep(0.05 * (2**attempt))


async def update_step(
    db: aiosqlite.Connection, workflow_id: str, skill_name: str, **fields: Any
) -> None:
    """Update one workflow step using a fixed allow-list of columns."""
    updates = {key: value for key, value in fields.items() if key in _STEP_FIELDS}
    if not updates:
        return
    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = [_encode_value(key, value) for key, value in updates.items()]
    values.extend((workflow_id, skill_name))
    await db.execute(
        f"UPDATE workflow_steps SET {assignments} WHERE workflow_id = ? AND skill_name = ?",
        values,
    )
    await db.commit()


async def list_logs(
    db: aiosqlite.Connection, workflow_id: str, limit: int = 500
) -> list[dict[str, Any]]:
    limit = min(5000, max(1, int(limit)))
    cursor = await db.execute(
        """
        SELECT * FROM (
            SELECT * FROM workflow_logs
            WHERE workflow_id = ?
            ORDER BY id DESC LIMIT ?
        ) ORDER BY id
        """,
        (workflow_id, limit),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def create_checkpoint(
    db: aiosqlite.Connection,
    workflow_id: str,
    step_name: str,
    checkpoint_type: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    await db.execute(
        "UPDATE checkpoints SET status = 'superseded' WHERE workflow_id = ? AND status = 'pending'",
        (workflow_id,),
    )
    cursor = await db.execute(
        """
        INSERT INTO checkpoints (workflow_id, step_name, checkpoint_type, data)
        VALUES (?, ?, ?, ?)
        """,
        (workflow_id, step_name, checkpoint_type, _encode_value("data", data or {})),
    )
    await db.commit()
    return {
        "id": cursor.lastrowid,
        "workflow_id": workflow_id,
        "step_name": step_name,
        "checkpoint_type": checkpoint_type,
        "data": data or {},
        "status": "pending",
    }


async def get_pending_checkpoint(
    db: aiosqlite.Connection, workflow_id: str
) -> dict[str, Any] | None:
    cursor = await db.execute(
        """
        SELECT * FROM checkpoints
        WHERE workflow_id = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
        """,
        (workflow_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    item = dict(row)
    item["data"] = _json_load(item.get("data"), {})
    item["response"] = _json_load(item.get("response"), None)
    return item


async def resolve_checkpoint_record(
    db: aiosqlite.Connection,
    checkpoint_id: int,
    response: dict[str, Any],
) -> None:
    await db.execute(
        """
        UPDATE checkpoints
        SET response = ?, status = 'resolved', resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (_encode_value("response", response), checkpoint_id),
    )
    await db.commit()


async def reset_workflow(
    db: aiosqlite.Connection, workflow_id: str, *, from_step: str | None = None
) -> None:
    """Reset all steps, or one step and everything after it, for another run."""
    if from_step:
        cursor = await db.execute(
            "SELECT step_order FROM workflow_steps WHERE workflow_id = ? AND skill_name = ?",
            (workflow_id, from_step),
        )
        row = await cursor.fetchone()
        if row is None:
            raise KeyError(from_step)
        await db.execute(
            """
            UPDATE workflow_steps
            SET status = 'pending', output_files = '[]', started_at = NULL,
                completed_at = NULL, error_message = NULL
            WHERE workflow_id = ? AND step_order >= ?
            """,
            (workflow_id, row[0]),
        )
    else:
        await db.execute(
            """
            UPDATE workflow_steps
            SET status = 'pending', output_files = '[]', started_at = NULL,
                completed_at = NULL, error_message = NULL
            WHERE workflow_id = ?
            """,
            (workflow_id,),
        )
    await db.execute(
        "DELETE FROM checkpoints WHERE workflow_id = ?", (workflow_id,)
    )
    await db.execute(
        """
        UPDATE workflows SET status = 'pending', current_step = NULL,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """,
        (workflow_id,),
    )
    await db.commit()


async def delete_workflow(db: aiosqlite.Connection, workflow_id: str) -> None:
    for table in ("checkpoints", "workflow_logs", "workflow_steps"):
        await db.execute(f"DELETE FROM {table} WHERE workflow_id = ?", (workflow_id,))
    await db.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
    await db.commit()


async def get_setting(key: str, default: str = "") -> str:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return default if row is None else str(row[0])
    finally:
        await db.close()


async def get_all_settings() -> dict[str, str]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value FROM settings ORDER BY key")
        return {str(row[0]): str(row[1]) for row in await cursor.fetchall()}
    finally:
        await db.close()


async def save_settings(data: dict[str, str]) -> None:
    db = await get_db()
    try:
        for key, value in data.items():
            if not isinstance(key, str) or not key:
                continue
            clean_value = "" if value is None else str(value)
            await db.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, clean_value),
            )
        await db.commit()
    finally:
        await db.close()


async def append_log(
    workflow_id: str,
    message: str,
    *,
    step_name: str | None = None,
    level: str = "info",
) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO workflow_logs (workflow_id, step_name, level, message) VALUES (?, ?, ?, ?)",
            (workflow_id, step_name, level, message),
        )
        await db.commit()
    finally:
        await db.close()


async def export_workflow_data(wf_id: str) -> dict[str, Any] | None:
    db = await get_db()
    try:
        workflow = await get_workflow(db, wf_id)
        if workflow is None:
            return None
        cursor = await db.execute(
            "SELECT * FROM workflow_logs WHERE workflow_id = ? ORDER BY id", (wf_id,)
        )
        logs = [dict(row) for row in await cursor.fetchall()]
        cursor = await db.execute(
            "SELECT * FROM checkpoints WHERE workflow_id = ? ORDER BY id", (wf_id,)
        )
        checkpoints = []
        for row in await cursor.fetchall():
            item = dict(row)
            item["data"] = _json_load(item.get("data"), {})
            item["response"] = _json_load(item.get("response"), None)
            checkpoints.append(item)
        return {"workflow": workflow, "logs": logs, "checkpoints": checkpoints}
    finally:
        await db.close()


async def import_workflow_data(
    data: dict[str, Any], new_id: str, workspace_dir: str
) -> None:
    workflow = dict(data.get("workflow") or {})
    if not workflow:
        raise ValueError("Import data does not contain a workflow")
    workflow.update({"id": new_id, "workspace_dir": workspace_dir, "status": "pending"})
    for step in workflow.get("steps", []):
        step.pop("id", None)
        step["workflow_id"] = new_id

    db = await get_db()
    try:
        await create_workflow(db, workflow)
        for log_item in data.get("logs", []):
            await db.execute(
                """
                INSERT INTO workflow_logs (workflow_id, step_name, level, message, created_at)
                VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
                """,
                (
                    new_id,
                    log_item.get("step_name"),
                    log_item.get("level", "info"),
                    log_item.get("message", ""),
                    log_item.get("created_at"),
                ),
            )
        for checkpoint in data.get("checkpoints", []):
            await db.execute(
                """
                INSERT INTO checkpoints
                    (workflow_id, step_name, checkpoint_type, data, response,
                     status, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?)
                """,
                (
                    new_id,
                    checkpoint.get("step_name", ""),
                    checkpoint.get("checkpoint_type", "approve"),
                    _encode_value("data", checkpoint.get("data", {})),
                    _encode_value("response", checkpoint.get("response"))
                    if checkpoint.get("response") is not None
                    else None,
                    checkpoint.get("status", "pending"),
                    checkpoint.get("created_at"),
                    checkpoint.get("resolved_at"),
                ),
            )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
