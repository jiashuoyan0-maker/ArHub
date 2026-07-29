"""Declarative extension discovery for the ArHub open workspace layer.

Extensions are data-only in schema v1. The registry never imports extension
Python modules or executes commands from a manifest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
MAX_MANIFEST_BYTES = 256 * 1024
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


class ExtensionRegistry:
    def __init__(
        self,
        builtin_dir: str | Path,
        user_dir: str | Path,
        schema_path: str | Path,
    ) -> None:
        self.builtin_dir = Path(builtin_dir)
        self.user_dir = Path(user_dir)
        self.schema_path = Path(schema_path)

    def schema(self) -> dict[str, Any]:
        try:
            return json.loads(self.schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "schema_version": SCHEMA_VERSION,
                "error": f"Extension schema is unavailable: {type(exc).__name__}",
            }

    def snapshot(self) -> dict[str, Any]:
        extensions: list[dict[str, Any]] = []
        profiles: list[dict[str, Any]] = []
        commands: list[dict[str, Any]] = []
        tool_adapters: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        extension_ids: set[str] = set()
        contribution_ids: set[str] = set()

        for source, root in (("builtin", self.builtin_dir), ("user", self.user_dir)):
            for manifest_path in self._manifest_paths(root):
                try:
                    manifest = self._read_manifest(manifest_path)
                    extension = self._normalize_extension(manifest, source)
                    extension_id = extension["id"]
                    if extension_id in extension_ids:
                        raise ValueError(f"duplicate extension id: {extension_id}")
                    extension_ids.add(extension_id)

                    contributions = manifest.get("contributes") or {}
                    extension_profiles = self._normalize_profiles(
                        extension_id,
                        contributions.get("agent_profiles") or [],
                        source,
                        contribution_ids,
                    )
                    extension_commands = self._normalize_commands(
                        extension_id,
                        contributions.get("commands") or [],
                        source,
                        contribution_ids,
                    )
                    extension_tools = self._normalize_tool_adapters(
                        extension_id,
                        contributions.get("tool_adapters") or [],
                        source,
                        contribution_ids,
                    )

                    extension["contribution_counts"] = {
                        "agent_profiles": len(extension_profiles),
                        "commands": len(extension_commands),
                        "tool_adapters": len(extension_tools),
                    }
                    extensions.append(extension)
                    profiles.extend(extension_profiles)
                    commands.extend(extension_commands)
                    tool_adapters.extend(extension_tools)
                except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                    errors.append(
                        {
                            "source": source,
                            "manifest": manifest_path.parent.name,
                            "message": str(exc)[:240],
                        }
                    )

        return {
            "schema_version": SCHEMA_VERSION,
            "extensions": extensions,
            "agent_profiles": profiles,
            "commands": commands,
            "tool_adapters": tool_adapters,
            "errors": errors,
            "policy": {
                "manifest_only": True,
                "third_party_code_execution": False,
            },
        }

    @staticmethod
    def _manifest_paths(root: Path) -> list[Path]:
        try:
            if not root.is_dir():
                return []
            return sorted(
                child / "manifest.json"
                for child in root.iterdir()
                if child.is_dir() and (child / "manifest.json").is_file()
            )
        except OSError:
            return []

    @staticmethod
    def _read_manifest(path: Path) -> dict[str, Any]:
        if path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError("manifest exceeds 256 KiB")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("manifest root must be an object")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version: {payload.get('schema_version')!r}"
            )
        return payload

    @staticmethod
    def _validate_id(value: Any, label: str) -> str:
        if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
            raise ValueError(f"invalid {label}: {value!r}")
        return value

    def _normalize_extension(
        self,
        manifest: dict[str, Any],
        source: str,
    ) -> dict[str, Any]:
        extension_id = self._validate_id(manifest.get("id"), "extension id")
        name = manifest.get("name")
        version = manifest.get("version")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("extension name is required")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("extension version is required")
        return {
            "id": extension_id,
            "name": name.strip()[:80],
            "version": version.strip()[:32],
            "description": str(manifest.get("description") or "")[:240],
            "license": str(manifest.get("license") or "")[:48],
            "homepage": str(manifest.get("homepage") or "")[:240],
            "source": source,
        }

    def _normalize_profiles(
        self,
        extension_id: str,
        values: Any,
        source: str,
        contribution_ids: set[str],
    ) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            raise ValueError("contributes.agent_profiles must be an array")
        result: list[dict[str, Any]] = []
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("agent profile must be an object")
            local_id = self._validate_id(value.get("id"), "agent profile id")
            qualified_id = f"{extension_id}/{local_id}"
            self._claim_contribution_id(qualified_id, contribution_ids)
            mode = value.get("mode", "agent")
            if mode not in {"agent", "lite"}:
                raise ValueError(f"invalid agent profile mode: {mode!r}")
            label = value.get("label")
            if not isinstance(label, str) or not label.strip():
                raise ValueError("agent profile label is required")
            capabilities = value.get("capabilities") or []
            if not isinstance(capabilities, list) or not all(
                isinstance(item, str) for item in capabilities
            ):
                raise ValueError("agent profile capabilities must be strings")
            result.append(
                {
                    "id": qualified_id,
                    "extension_id": extension_id,
                    "local_id": local_id,
                    "label": label.strip()[:48],
                    "description": str(value.get("description") or "")[:180],
                    "mode": mode,
                    "accent": str(value.get("accent") or "#0a84ff")[:16],
                    "capabilities": capabilities[:12],
                    "system_prompt": str(value.get("system_prompt") or "")[:12000],
                    "source": source,
                }
            )
        return result

    def _normalize_commands(
        self,
        extension_id: str,
        values: Any,
        source: str,
        contribution_ids: set[str],
    ) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            raise ValueError("contributes.commands must be an array")
        result: list[dict[str, Any]] = []
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("command must be an object")
            local_id = self._validate_id(value.get("id"), "command id")
            qualified_id = f"{extension_id}/{local_id}"
            self._claim_contribution_id(qualified_id, contribution_ids)
            label = value.get("label")
            prompt = value.get("prompt")
            if not isinstance(label, str) or not label.strip():
                raise ValueError("command label is required")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("command prompt is required")
            result.append(
                {
                    "id": qualified_id,
                    "extension_id": extension_id,
                    "local_id": local_id,
                    "label": label.strip()[:64],
                    "description": str(value.get("description") or "")[:180],
                    "prompt": prompt[:12000],
                    "source": source,
                }
            )
        return result

    def _normalize_tool_adapters(
        self,
        extension_id: str,
        values: Any,
        source: str,
        contribution_ids: set[str],
    ) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            raise ValueError("contributes.tool_adapters must be an array")
        result: list[dict[str, Any]] = []
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("tool adapter must be an object")
            local_id = self._validate_id(value.get("id"), "tool adapter id")
            qualified_id = f"{extension_id}/{local_id}"
            self._claim_contribution_id(qualified_id, contribution_ids)
            label = value.get("label")
            if not isinstance(label, str) or not label.strip():
                raise ValueError("tool adapter label is required")
            result.append(
                {
                    "id": qualified_id,
                    "extension_id": extension_id,
                    "local_id": local_id,
                    "label": label.strip()[:64],
                    "description": str(value.get("description") or "")[:180],
                    "protocol": str(value.get("protocol") or "manifest-v1")[:32],
                    "enabled": False,
                    "source": source,
                }
            )
        return result

    @staticmethod
    def _claim_contribution_id(
        qualified_id: str,
        contribution_ids: set[str],
    ) -> None:
        if qualified_id in contribution_ids:
            raise ValueError(f"duplicate contribution id: {qualified_id}")
        contribution_ids.add(qualified_id)
