"""Backend configuration.

Recovered values from the installed build. Paths resolve relative to the
repository layout so the backend works from a source checkout:

    <repo>/backend/config.py   -> PROJECT_ROOT = <repo>
    runtime tools              -> <repo>/runtime or <install>/runtime
    user data                  -> %APPDATA%/ArHub by default
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# True when running inside the packaged Electron desktop app.
IS_DESKTOP = True

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Bundled runtimes. Source checkouts use <repo>/runtime; packaged installs use
# <install>/runtime next to resources/.
if PROJECT_ROOT.name == "app" and PROJECT_ROOT.parent.name == "resources":
    _DEFAULT_RUNTIME_BASE = PROJECT_ROOT.parent.parent / "runtime"
else:
    _DEFAULT_RUNTIME_BASE = PROJECT_ROOT / "runtime"
_RUNTIME_BASE = Path(os.environ.get("ARHUB_RUNTIME_DIR", _DEFAULT_RUNTIME_BASE))
RUNTIME_PYTHON = _RUNTIME_BASE / "python" / "python.exe"
RUNTIME_NODE = _RUNTIME_BASE / "node"
RUNTIME_PANDOC = _RUNTIME_BASE / "pandoc" / "pandoc.exe"
RUNTIME_TEXLIVE = _RUNTIME_BASE / "texlive"
RUNTIME_DRAWIO = _RUNTIME_BASE / "draw.io"
PANDOC_BIN = RUNTIME_PANDOC
CLAUDE_BIN = RUNTIME_NODE / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"

# Frontend build output served by FastAPI.
FRONTEND_DIST = Path(os.environ.get("ARHUB_FRONTEND_DIST", PROJECT_ROOT / "dist"))

# Content directories.
SKILLS_DIR = PROJECT_ROOT / "skills"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
TOOLS_DIR = PROJECT_ROOT / "tools"

# Per-user state.
_DEFAULT_APPDATA_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "ArHub"
APPDATA_DIR = Path(os.environ.get("ARHUB_DATA_DIR", _DEFAULT_APPDATA_DIR))
WORKSPACES_DIR = APPDATA_DIR / "workspaces"
DB_PATH = APPDATA_DIR / "db" / "aris.db"

# HTTP listen port for the embedded backend.
API_PORT = int(os.environ.get("ARHUB_API_PORT", "18088"))
