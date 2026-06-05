"""FastMCP server entrypoint. Registers all v0.1.0 tools over stdio."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP("fedramp-docs")


@mcp.tool()
def list_ksis(theme: str | None = None) -> dict:
    """Enumerate FedRAMP 20x Key Security Indicators (KSIs).

    Args:
        theme: Optional theme short_name to filter by (e.g. 'AFR', 'IAM', 'CMT').
    """
    return tools.list_ksis(theme)


@mcp.tool()
def get_ksi(id: str) -> dict:
    """Get full text of a single KSI indicator.

    Args:
        id: The KSI indicator ID, e.g. 'KSI-AFR-01'.
    """
    return tools.get_ksi(id)


@mcp.tool()
def list_frrs(status: str | None = None) -> dict:
    """Enumerate 20x FedRAMP Requirements & Rules (FRR) sections.

    Args:
        status: Optional filter on effective.current_status (e.g. 'Open Beta', 'GA').
    """
    return tools.list_frrs(status)


@mcp.tool()
def get_frr_section(short_name: str) -> dict:
    """Get full text of a 20x-effective FRR section.

    Args:
        short_name: Section short_name, e.g. 'ADS', 'CCM', 'FSI'.
    """
    return tools.get_frr_section(short_name)


@mcp.tool()
def get_definition(term_or_id: str) -> dict:
    """Look up a FedRAMP Definition by ID, term, or alt name.

    Args:
        term_or_id: An FRD ID (e.g. 'FRD-ACV'), the definition term, or an alt spelling.
    """
    return tools.get_definition(term_or_id)


@mcp.tool()
def search(query: str, scope: str | None = None) -> dict:
    """Full-text search across KSIs, FRRs, and FRDs.

    Args:
        query: Search string (case-insensitive substring match).
        scope: Optional 'KSI' | 'FRR' | 'FRD' to narrow the search.
    """
    return tools.search(query, scope)


@mcp.tool()
def get_source_info() -> dict:
    """Return metadata about the active FRMR snapshot.

    Reports upstream commit, frmr_version, fetched_at, and whether the active
    source is the bundled snapshot or a user-refreshed cache. Run
    `fedramp-docs-mcp refresh` from the CLI to update.
    """
    return tools.get_source_info()


def run() -> None:
    mcp.run()
