"""Tool implementations.

v0.1.0 — 20x only. Rev 5 deferred to v0.3.0.

Two tools are fully implemented as samples (`get_source_info`, `get_definition`)
so the patterns — citation wrapping, JSON path attribution, error shape — are
visible. The remaining tools are stubs that raise NotImplementedError; they'll
be implemented in M2 once the scaffolding pattern is approved.
"""

from __future__ import annotations

from typing import Any

from .cite import make_source, with_source
from .loader import load_frmr, load_source_version, source_is_cached


def get_source_info() -> dict[str, Any]:
    """Return metadata about the active FRMR snapshot."""
    sv = load_source_version()
    return {
        "active_snapshot": "user_cache" if source_is_cached() else "bundled",
        "upstream_repo": sv.get("upstream_repo"),
        "upstream_url": sv.get("upstream_url"),
        "upstream_commit": sv.get("upstream_commit"),
        "upstream_raw_url": sv.get("upstream_raw_url"),
        "frmr_version": sv.get("frmr_version"),
        "frmr_last_updated": sv.get("frmr_last_updated"),
        "fetched_at": sv.get("fetched_at"),
        "note": (
            "Unofficial MCP server for the public FedRAMP 20x machine-readable "
            "documentation. Not affiliated with FedRAMP, GSA, or the U.S. government. "
            "Run `fedramp-docs-mcp refresh` to update the snapshot from upstream."
        ),
    }


def get_definition(term_or_id: str) -> dict[str, Any]:
    """Look up a FedRAMP Definition (FRD) by ID, term, or alt name.

    Match order: FRD ID (case-insensitive) → term (case-insensitive) → alts list.
    """
    frmr = load_frmr()
    defs = frmr.get("FRD", {}).get("data", {}).get("both", {})
    needle = term_or_id.strip().lower()

    for def_id, entry in defs.items():
        if def_id.lower() == needle:
            return with_source({"id": def_id, **entry}, f"/FRD/data/both/{def_id}")

    for def_id, entry in defs.items():
        if entry.get("term", "").lower() == needle:
            return with_source({"id": def_id, **entry}, f"/FRD/data/both/{def_id}")

    for def_id, entry in defs.items():
        alts = [a.lower() for a in (entry.get("alts") or [])]
        if needle in alts:
            return with_source({"id": def_id, **entry}, f"/FRD/data/both/{def_id}")

    return {
        "error": "not_found",
        "query": term_or_id,
        "hint": (
            "No FRD entry matched. Try the FRD- ID, the exact term, or use "
            "search(query, scope='FRD') for substring matching."
        ),
        "_source": make_source("/FRD/data/both"),
    }


# --- Stubs (implementation scheduled for v0.1.0 M2) ---


def list_ksis(theme: str | None = None) -> dict[str, Any]:
    """Enumerate FedRAMP 20x Key Security Indicators.

    Args:
        theme: Optional theme short_name (e.g. 'AFR', 'IAM', 'CMT') to narrow results.
    """
    raise NotImplementedError("list_ksis: scheduled for v0.1.0 M2")


def get_ksi(id: str) -> dict[str, Any]:
    """Get full text of a single KSI indicator (e.g. 'KSI-AFR-01')."""
    raise NotImplementedError("get_ksi: scheduled for v0.1.0 M2")


def list_frrs(status: str | None = None) -> dict[str, Any]:
    """Enumerate 20x FRR sections with their effective status.

    Args:
        status: Optional filter on effective.current_status (e.g. 'Open Beta').
    """
    raise NotImplementedError("list_frrs: scheduled for v0.1.0 M2")


def get_frr_section(short_name: str) -> dict[str, Any]:
    """Get full text of a 20x-effective FRR section (e.g. 'ADS', 'CCM', 'FSI')."""
    raise NotImplementedError("get_frr_section: scheduled for v0.1.0 M2")


def search(query: str, scope: str | None = None) -> dict[str, Any]:
    """Full-text search across KSI / FRR / FRD.

    Args:
        query: Case-insensitive substring to match.
        scope: Optional 'KSI' | 'FRR' | 'FRD' to narrow.
    """
    raise NotImplementedError("search: scheduled for v0.1.0 M2")
