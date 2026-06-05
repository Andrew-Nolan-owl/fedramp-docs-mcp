"""Load FRMR JSON and SOURCE_VERSION.

The active snapshot is the user cache if it exists (written by the refresh CLI),
otherwise the bundled snapshot shipped inside the package. uvx environments are
often ephemeral, so refresh must write to a persistent user-cache location —
never to site-packages.
"""

from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Any

_CACHE_ENV = "FEDRAMP_DOCS_MCP_CACHE_DIR"
_FRMR_FILENAME = "FRMR.documentation.json"
_SOURCE_FILENAME = "SOURCE_VERSION.json"


def cache_dir() -> Path:
    """Return the user cache directory. Override with FEDRAMP_DOCS_MCP_CACHE_DIR."""
    override = os.environ.get(_CACHE_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "fedramp-docs-mcp"
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local) / "fedramp-docs-mcp" / "Cache"
    return Path.home() / ".cache" / "fedramp-docs-mcp"


def _bundled(filename: str) -> Path:
    return Path(str(files("fedramp_docs_mcp.data").joinpath(filename)))


def frmr_path() -> Path:
    """Path to the active FRMR JSON: user cache if present, else bundled snapshot."""
    cached = cache_dir() / _FRMR_FILENAME
    return cached if cached.exists() else _bundled(_FRMR_FILENAME)


def source_version_path() -> Path:
    cached = cache_dir() / _SOURCE_FILENAME
    return cached if cached.exists() else _bundled(_SOURCE_FILENAME)


def load_frmr() -> dict[str, Any]:
    with frmr_path().open("r", encoding="utf-8") as f:
        return json.load(f)


def load_source_version() -> dict[str, Any]:
    with source_version_path().open("r", encoding="utf-8") as f:
        return json.load(f)


def source_is_cached() -> bool:
    """True if the active source is from the user cache, False if from the bundled snapshot."""
    return (cache_dir() / _FRMR_FILENAME).exists()
