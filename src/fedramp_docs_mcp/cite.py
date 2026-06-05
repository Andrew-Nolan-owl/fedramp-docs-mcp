"""Citation wrapper.

Every tool response carries a `_source` block built here, so attribution is
structural — it can't be paraphrased away by the model.
"""

from __future__ import annotations

from typing import Any

from .loader import load_source_version, source_is_cached


def make_source(json_path: str) -> dict[str, Any]:
    """Build a `_source` block.

    Args:
        json_path: JSON Pointer-style path into FRMR (e.g. "/KSI/AFR/indicators/01").
    """
    sv = load_source_version()
    return {
        "file": "FRMR.documentation.json",
        "upstream_repo": sv.get("upstream_repo", "FedRAMP/docs"),
        "upstream_url": sv.get("upstream_url"),
        "upstream_commit": sv.get("upstream_commit"),
        "frmr_version": sv.get("frmr_version"),
        "frmr_last_updated": sv.get("frmr_last_updated"),
        "fetched_at": sv.get("fetched_at"),
        "json_path": json_path,
        "active_snapshot": "user_cache" if source_is_cached() else "bundled",
    }


def with_source(data: Any, json_path: str) -> dict[str, Any]:
    """Wrap a tool response with a `_source` block."""
    return {"data": data, "_source": make_source(json_path)}
