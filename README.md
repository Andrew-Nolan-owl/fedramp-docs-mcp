# fedramp-docs-mcp

An **unofficial** Model Context Protocol (MCP) server that exposes the public FedRAMP 20x machine-readable documentation (FRMR) as deterministic, citable lookup tools for AI assistants.

> ⚠️ **Not affiliated with FedRAMP, GSA, or the U.S. government.** This is a community-built tool. Data is sourced from the public GSA FedRAMP docs repository at https://github.com/FedRAMP/docs. The bundled `FRMR.documentation.json` is a U.S. government work in the public domain (17 U.S.C. § 105); this server's code is MIT-licensed.

## Why this exists

When using AI assistants to analyze, scope, or write about FedRAMP 20x requirements, the model can paraphrase FRMR content from memory and drift on numbers, IDs, dates, or definitions. This MCP server replaces that with structured lookups against the canonical JSON — every response carries a `_source` block pointing to the exact upstream commit and JSON path. The model literally cannot answer without citing the source.

## Install

> 📦 **PyPI release is planned but not yet published.** Install directly from this GitHub repo via `uvx` for now. The PyPI path below will work once v0.1.0 stabilizes.

### Install from GitHub (current path)

`uvx` can install directly from a git URL — no PyPI required, no clone needed:

```bash
uvx --from git+https://github.com/Andrew-Nolan-owl/fedramp-docs-mcp.git fedramp-docs-mcp --help
```

(Install `uv` first if needed: `brew install uv` on macOS, or see https://docs.astral.sh/uv/.)

You can pin to a specific tag or commit for reproducibility:

```bash
# pin to a tag
uvx --from git+https://github.com/Andrew-Nolan-owl/fedramp-docs-mcp.git@v0.1.0 fedramp-docs-mcp

# pin to a commit SHA
uvx --from git+https://github.com/Andrew-Nolan-owl/fedramp-docs-mcp.git@<sha> fedramp-docs-mcp
```

### Install from PyPI (planned, not yet available)

Once v0.1.0 is published to PyPI, this will be the simpler path:

```bash
# Not yet — coming with v0.1.0 PyPI release
uvx fedramp-docs-mcp
```

## Configure your MCP client

### Claude Code / Claude Desktop

Add to your MCP client config (e.g., `~/.claude.json`):

```json
{
  "mcpServers": {
    "fedramp-docs": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Andrew-Nolan-owl/fedramp-docs-mcp.git",
        "fedramp-docs-mcp"
      ]
    }
  }
}
```

Once the PyPI release ships, the config simplifies to:

```json
{
  "mcpServers": {
    "fedramp-docs": {
      "command": "uvx",
      "args": ["fedramp-docs-mcp"]
    }
  }
}
```

Restart your client. The tools appear automatically; verify with `/mcp` in Claude Code.

## Available tools (v0.1.0 — 20x only)

| Tool | Purpose |
|---|---|
| `list_ksis(theme?)` | Enumerate Key Security Indicators (~60 across 11 themes) |
| `get_ksi(id)` | Full text of a KSI indicator by ID (e.g. `KSI-AFR-01`) |
| `list_frrs(status?)` | Enumerate FedRAMP Requirements & Rules sections with effective status |
| `get_frr_section(short_name)` | Full text of an FRR section (e.g. `ADS`, `CCM`) |
| `get_definition(term_or_id)` | FedRAMP Definition lookup by ID, term, or alt |
| `search(query, scope?)` | Full-text search across KSIs, FRRs, and FRDs |
| `get_source_info()` | Vendored snapshot metadata — upstream commit, fetched_at, etc. |

Every response includes `_source`:

```json
{
  "_source": {
    "file": "FRMR.documentation.json",
    "upstream_commit": "a06fa8f9b103c0346895fb669b721962f5891bb6",
    "upstream_url": "https://github.com/FedRAMP/docs",
    "last_updated": "2026-04-08",
    "json_path": "/KSI/AFR/indicators/01"
  }
}
```

## Refreshing the FRMR snapshot

This server ships with a vendored snapshot of `FRMR.documentation.json` pinned to a specific upstream commit. To pull the latest:

```bash
uvx fedramp-docs-mcp refresh
```

Refresh is a CLI action (not an MCP tool) because it mutates local state across all future sessions. Reference servers (`fetch`, `time`) follow the same pattern.

Run `refresh` when:
- You're starting a new work session that needs current data
- Upstream has new commits at https://github.com/FedRAMP/docs
- `get_source_info` shows a stale `fetched_at`

## Scope

**v0.1.0** surfaces only 20x-effective content (items where `effective.20x.is != "no"` in FRMR). Rev 5 expansion is planned for v0.3.0. See [`ROADMAP.md`](./ROADMAP.md) if present, or the GitHub issues.

## Design notes

- **Framework**: FastMCP (high-level decorator API in the official `mcp` Python SDK)
- **Distribution**: PyPI, runnable via `uvx`
- **Data**: Vendored snapshot + explicit `refresh` CLI (deterministic by default, fresh on demand)
- **Citations**: Structural — every response carries `_source` so attribution can't be dropped or paraphrased

## Development

```bash
git clone https://github.com/Andrew-Nolan-owl/fedramp-docs-mcp.git
cd fedramp-docs-mcp
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## Contributing

Issues and PRs welcome. This is an alpha-stage tool — tool ergonomics, error messages, and search ranking are all open to iteration.

## License

MIT (see [`LICENSE`](./LICENSE)). The bundled FRMR JSON is a U.S. government work in the public domain.
