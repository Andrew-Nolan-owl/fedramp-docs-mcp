"""Tool implementations.

v0.1.0 — 20x only. Rev 5 deferred to v0.3.0.

Every tool returns either a `with_source(...)`-wrapped dict (happy path) or a
dict with `error` plus `_source` (failure path). Tools never raise on bad
input — they return a structured error so MCP clients get a usable response.
"""

from __future__ import annotations

from typing import Any

from .cite import make_source, with_source
from .loader import load_frmr, load_source_version, source_is_cached

_SNIPPET_WIDTH = 200
_VALID_SEARCH_SCOPES = {"KSI", "FRR", "FRD"}


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


def list_ksis(theme: str | None = None) -> dict[str, Any]:
    """Enumerate FedRAMP 20x Key Security Indicators.

    Args:
        theme: Optional theme short_name (e.g. 'AFR', 'IAM', 'CMT'). Case-insensitive.
    """
    frmr = load_frmr()
    ksi = frmr.get("KSI", {})

    if theme:
        theme_upper = theme.strip().upper()
        if theme_upper not in ksi:
            return {
                "error": "unknown_theme",
                "query": theme,
                "available_themes": sorted(ksi.keys()),
                "_source": make_source("/KSI"),
            }
        themes_to_list = {theme_upper: ksi[theme_upper]}
    else:
        themes_to_list = ksi

    indicators: list[dict[str, Any]] = []
    for theme_code, theme_data in themes_to_list.items():
        for ind_id, ind_data in (theme_data.get("indicators") or {}).items():
            indicators.append(
                {
                    "id": ind_id,
                    "fka": ind_data.get("fka"),
                    "theme": theme_code,
                    "theme_name": theme_data.get("name"),
                    "name": ind_data.get("name"),
                    "controls": ind_data.get("controls", []),
                }
            )

    return with_source(
        {
            "count": len(indicators),
            "theme_filter": theme.strip().upper() if theme else None,
            "indicators": indicators,
        },
        "/KSI" if not theme else f"/KSI/{theme.strip().upper()}",
    )


def get_ksi(id: str) -> dict[str, Any]:
    """Get full text of a single KSI indicator.

    Args:
        id: Current ID (e.g. 'KSI-AFR-ADS') or legacy `fka` (e.g. 'KSI-AFR-03').
    """
    frmr = load_frmr()
    ksi = frmr.get("KSI", {})
    needle = id.strip().upper()

    for theme_code, theme_data in ksi.items():
        for ind_id, ind_data in (theme_data.get("indicators") or {}).items():
            if ind_id.upper() == needle:
                return with_source(
                    {
                        "id": ind_id,
                        "theme": theme_code,
                        "theme_name": theme_data.get("name"),
                        **ind_data,
                    },
                    f"/KSI/{theme_code}/indicators/{ind_id}",
                )

    for theme_code, theme_data in ksi.items():
        for ind_id, ind_data in (theme_data.get("indicators") or {}).items():
            if (ind_data.get("fka") or "").upper() == needle:
                return with_source(
                    {
                        "id": ind_id,
                        "theme": theme_code,
                        "theme_name": theme_data.get("name"),
                        "matched_via": "fka",
                        **ind_data,
                    },
                    f"/KSI/{theme_code}/indicators/{ind_id}",
                )

    return {
        "error": "not_found",
        "query": id,
        "hint": (
            "Use list_ksis() to see all KSI IDs. Current IDs look like 'KSI-AFR-ADS'; "
            "legacy IDs ('KSI-AFR-03') also resolve via the indicator's `fka` field."
        ),
        "_source": make_source("/KSI"),
    }


def list_frrs(status: str | None = None) -> dict[str, Any]:
    """Enumerate 20x-effective FRR sections.

    Args:
        status: Optional case-insensitive filter on effective.20x.current_status
            (e.g. 'Phase 2 Pilot', 'Open Beta', 'GA').
    """
    frmr = load_frmr()
    frr = frmr.get("FRR", {})

    sections: list[dict[str, Any]] = []
    for short_name, sec in frr.items():
        info = sec.get("info", {})
        e20 = (info.get("effective") or {}).get("20x") or {}
        if e20.get("is") == "no":
            continue

        cur_status = e20.get("current_status")
        if status and (cur_status or "").lower() != status.strip().lower():
            continue

        sections.append(
            {
                "short_name": short_name,
                "name": info.get("name"),
                "web_name": info.get("web_name"),
                "effective_20x": {
                    "is": e20.get("is"),
                    "current_status": cur_status,
                    "start_date": e20.get("start_date"),
                    "end_date": e20.get("end_date"),
                },
                "labels": info.get("labels", []),
            }
        )

    return with_source(
        {
            "count": len(sections),
            "status_filter": status.strip() if status else None,
            "sections": sections,
        },
        "/FRR",
    )


def get_frr_section(short_name: str) -> dict[str, Any]:
    """Get full text of a 20x-effective FRR section.

    Returns the section's `info` (including effective metadata) plus its rule
    data combined from both the 20x-only slice and the both-versions slice.

    Args:
        short_name: Section short_name (e.g. 'ADS', 'CCM', 'FSI'). Case-insensitive.
    """
    frmr = load_frmr()
    frr = frmr.get("FRR", {})
    needle = short_name.strip().upper()

    if needle not in frr:
        return {
            "error": "not_found",
            "query": short_name,
            "available_sections": sorted(frr.keys()),
            "_source": make_source("/FRR"),
        }

    sec = frr[needle]
    info = sec.get("info", {})
    data = sec.get("data", {})
    e20 = (info.get("effective") or {}).get("20x") or {}

    if e20.get("is") == "no":
        return {
            "error": "not_20x_effective",
            "short_name": needle,
            "rev5_effective_is": (info.get("effective") or {}).get("rev5", {}).get("is"),
            "hint": "This section is not effective in 20x. Rev 5 surfacing arrives in v0.3.0.",
            "_source": make_source(f"/FRR/{needle}"),
        }

    return with_source(
        {
            "short_name": needle,
            "name": info.get("name"),
            "web_name": info.get("web_name"),
            "effective_20x": e20,
            "labels": info.get("labels", []),
            "front_matter": info.get("front_matter"),
            "rules_20x_only": data.get("20x") or {},
            "rules_both": data.get("both") or {},
        },
        f"/FRR/{needle}",
    )


def search(query: str, scope: str | None = None) -> dict[str, Any]:
    """Full-text (case-insensitive substring) search across KSI / FRR / FRD.

    Args:
        query: Search string. Empty/whitespace returns an error.
        scope: Optional 'KSI' | 'FRR' | 'FRD' (case-insensitive) to narrow scope.
    """
    needle = query.strip().lower()
    if not needle:
        return {
            "error": "empty_query",
            "_source": make_source("/"),
        }

    scope_filter: str | None = None
    if scope:
        scope_filter = scope.strip().upper()
        if scope_filter not in _VALID_SEARCH_SCOPES:
            return {
                "error": "invalid_scope",
                "query_scope": scope,
                "valid_scopes": sorted(_VALID_SEARCH_SCOPES),
                "_source": make_source("/"),
            }

    frmr = load_frmr()
    hits: list[dict[str, Any]] = []

    if scope_filter in (None, "KSI"):
        for theme_code, theme_data in frmr.get("KSI", {}).items():
            for ind_id, ind_data in (theme_data.get("indicators") or {}).items():
                text = _join_searchable(
                    ind_data.get("name"),
                    ind_data.get("reference"),
                    ind_data.get("statement"),
                )
                if needle in text.lower():
                    hits.append(
                        {
                            "scope": "KSI",
                            "id": ind_id,
                            "title": ind_data.get("name"),
                            "snippet": _snippet(text, needle),
                            "json_path": f"/KSI/{theme_code}/indicators/{ind_id}",
                        }
                    )

    if scope_filter in (None, "FRR"):
        for short_name, sec in frmr.get("FRR", {}).items():
            info = sec.get("info", {})
            if (info.get("effective") or {}).get("20x", {}).get("is") == "no":
                continue
            data = sec.get("data", {})
            for slice_key in ("20x", "both"):
                subcats = data.get(slice_key) or {}
                if not isinstance(subcats, dict):
                    continue
                for subcat_id, rules in subcats.items():
                    if not isinstance(rules, dict):
                        continue
                    for rule_id, rule_data in rules.items():
                        if not isinstance(rule_data, dict):
                            continue
                        text = _join_searchable(
                            rule_data.get("name"),
                            rule_data.get("statement"),
                        )
                        if needle in text.lower():
                            hits.append(
                                {
                                    "scope": "FRR",
                                    "id": rule_id,
                                    "section": short_name,
                                    "title": rule_data.get("name"),
                                    "snippet": _snippet(text, needle),
                                    "json_path": (
                                        f"/FRR/{short_name}/data/{slice_key}/"
                                        f"{subcat_id}/{rule_id}"
                                    ),
                                }
                            )

    if scope_filter in (None, "FRD"):
        defs = frmr.get("FRD", {}).get("data", {}).get("both", {})
        for def_id, entry in defs.items():
            text = _join_searchable(
                entry.get("term"),
                " ".join(entry.get("alts") or []) or None,
                entry.get("definition"),
            )
            if needle in text.lower():
                hits.append(
                    {
                        "scope": "FRD",
                        "id": def_id,
                        "title": entry.get("term"),
                        "snippet": _snippet(text, needle),
                        "json_path": f"/FRD/data/both/{def_id}",
                    }
                )

    return with_source(
        {
            "query": query,
            "scope": scope_filter or "ALL",
            "count": len(hits),
            "hits": hits,
        },
        "/",
    )


def _join_searchable(*parts: str | None) -> str:
    """Join non-empty parts with " · " — used as both the haystack and snippet source.

    Keeping the haystack and snippet source identical guarantees that any match
    in the searchable text is visible in the returned snippet.
    """
    return " · ".join(p for p in parts if p)


def _snippet(text: str, needle: str, width: int = _SNIPPET_WIDTH) -> str:
    """Return a short window of `text` centered on the first occurrence of `needle`."""
    if not text:
        return ""
    lower = text.lower()
    idx = lower.find(needle)
    if idx < 0:
        return text[:width] + ("..." if len(text) > width else "")
    start = max(0, idx - width // 2)
    end = min(len(text), idx + len(needle) + width // 2)
    return (
        ("..." if start > 0 else "")
        + text[start:end]
        + ("..." if end < len(text) else "")
    )
