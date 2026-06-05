"""Refresh CLI: pull the latest FRMR.documentation.json from upstream into the user cache.

Writes to a persistent user-cache directory (XDG_CACHE_HOME / ~/.cache /
LOCALAPPDATA), never to site-packages — uvx environments are often ephemeral.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

import httpx

from .loader import cache_dir

UPSTREAM_REPO = "FedRAMP/docs"
UPSTREAM_BRANCH = "main"
GITHUB_API = "https://api.github.com"


def _latest_commit() -> str:
    url = f"{GITHUB_API}/repos/{UPSTREAM_REPO}/commits/{UPSTREAM_BRANCH}"
    resp = httpx.get(
        url,
        timeout=30.0,
        headers={"Accept": "application/vnd.github+json"},
    )
    resp.raise_for_status()
    return resp.json()["sha"]


def _fetch_frmr(commit: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{commit}/FRMR.documentation.json"
    resp = httpx.get(url, timeout=60.0)
    resp.raise_for_status()
    return resp.content


def _validate(payload: bytes) -> dict:
    data = json.loads(payload)
    required = {"info", "FRD", "FRR", "KSI"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Upstream JSON missing required top-level keys: {sorted(missing)}")
    return data


def run() -> int:
    target_dir = cache_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Resolving latest upstream commit for {UPSTREAM_REPO}@{UPSTREAM_BRANCH}...")
    try:
        sha = _latest_commit()
    except Exception as e:
        print(f"ERROR: failed to query GitHub API: {e}", file=sys.stderr)
        return 1
    print(f"  -> {sha}")

    print(f"Fetching FRMR.documentation.json @ {sha[:10]}...")
    try:
        payload = _fetch_frmr(sha)
        parsed = _validate(payload)
    except Exception as e:
        print(f"ERROR: failed to fetch or validate FRMR: {e}", file=sys.stderr)
        return 1

    frmr_path = target_dir / "FRMR.documentation.json"
    source_path = target_dir / "SOURCE_VERSION.json"

    frmr_path.write_bytes(payload)
    source_meta = {
        "upstream_repo": UPSTREAM_REPO,
        "upstream_url": f"https://github.com/{UPSTREAM_REPO}",
        "upstream_commit": sha,
        "upstream_raw_url": (
            f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{sha}/FRMR.documentation.json"
        ),
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "frmr_version": parsed.get("info", {}).get("version"),
        "frmr_last_updated": parsed.get("info", {}).get("last_updated"),
    }
    source_path.write_text(json.dumps(source_meta, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {frmr_path}")
    print(f"Wrote {source_path}")
    print(
        f"FRMR version: {source_meta['frmr_version']}  "
        f"(last_updated {source_meta['frmr_last_updated']})"
    )
    return 0
