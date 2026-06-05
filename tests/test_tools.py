"""Tests for v0.1.0 tools. Stubs assert NotImplementedError until M2 lands."""

from __future__ import annotations

import pytest

from fedramp_docs_mcp import tools


class TestGetSourceInfo:
    def test_returns_required_fields(self):
        info = tools.get_source_info()
        for key in ("upstream_repo", "upstream_commit", "frmr_version", "frmr_last_updated"):
            assert info.get(key), f"missing {key}"

    def test_includes_unaffiliated_disclaimer(self):
        info = tools.get_source_info()
        note = info["note"].lower()
        assert "unofficial" in note
        assert "not affiliated" in note


class TestGetDefinition:
    def test_lookup_by_id(self):
        result = tools.get_definition("FRD-ACV")
        assert result["data"]["id"] == "FRD-ACV"
        assert "term" in result["data"]
        assert "definition" in result["data"]

    def test_lookup_by_id_case_insensitive(self):
        assert tools.get_definition("frd-acv")["data"]["id"] == "FRD-ACV"

    def test_lookup_by_term(self):
        assert tools.get_definition("Accepted Vulnerability")["data"]["id"] == "FRD-ACV"

    def test_lookup_by_alt(self):
        assert tools.get_definition("accepted vulnerabilities")["data"]["id"] == "FRD-ACV"

    def test_unknown_returns_error(self):
        result = tools.get_definition("DEFINITELY-NOT-A-REAL-TERM-12345")
        assert result.get("error") == "not_found"
        assert "_source" in result

    def test_response_includes_source(self):
        src = tools.get_definition("FRD-ACV")["_source"]
        assert src["file"] == "FRMR.documentation.json"
        assert "upstream_commit" in src
        assert src["json_path"].startswith("/FRD/")


class TestStubs:
    """Stubs raise NotImplementedError until M2."""

    @pytest.mark.parametrize(
        "fn,args",
        [
            (tools.list_ksis, ()),
            (tools.get_ksi, ("KSI-AFR-01",)),
            (tools.list_frrs, ()),
            (tools.get_frr_section, ("ADS",)),
            (tools.search, ("vulnerability",)),
        ],
    )
    def test_stub_raises(self, fn, args):
        with pytest.raises(NotImplementedError):
            fn(*args)
