"""Tests for v0.1.0 tools, run against the vendored FRMR snapshot."""

from __future__ import annotations

from fedramp_docs_mcp import tools

# ---------- get_source_info ----------


class TestGetSourceInfo:
    def test_returns_required_fields(self):
        info = tools.get_source_info()
        for key in ("upstream_repo", "upstream_commit", "frmr_version", "frmr_last_updated"):
            assert info.get(key), f"missing {key}"

    def test_includes_unaffiliated_disclaimer(self):
        note = tools.get_source_info()["note"].lower()
        assert "unofficial" in note
        assert "not affiliated" in note


# ---------- get_definition ----------


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


# ---------- list_ksis ----------


class TestListKsis:
    def test_no_filter_returns_all_indicators(self):
        result = tools.list_ksis()
        assert result["data"]["count"] > 0
        assert result["data"]["theme_filter"] is None
        ids = {i["id"] for i in result["data"]["indicators"]}
        assert any(i.startswith("KSI-AFR-") for i in ids)
        assert any(i.startswith("KSI-IAM-") for i in ids)

    def test_filter_by_theme(self):
        result = tools.list_ksis("AFR")
        assert result["data"]["theme_filter"] == "AFR"
        for ind in result["data"]["indicators"]:
            assert ind["theme"] == "AFR"
            assert ind["id"].startswith("KSI-AFR-")

    def test_theme_filter_case_insensitive(self):
        assert tools.list_ksis("afr")["data"]["theme_filter"] == "AFR"

    def test_unknown_theme_returns_error(self):
        result = tools.list_ksis("ZZZ")
        assert result.get("error") == "unknown_theme"
        assert "available_themes" in result
        assert "AFR" in result["available_themes"]

    def test_response_includes_source(self):
        src = tools.list_ksis()["_source"]
        assert src["json_path"] == "/KSI"


# ---------- get_ksi ----------


class TestGetKsi:
    def test_lookup_by_current_id(self):
        result = tools.get_ksi("KSI-AFR-ADS")
        assert result["data"]["id"] == "KSI-AFR-ADS"
        assert result["data"]["theme"] == "AFR"
        assert "statement" in result["data"]
        assert "matched_via" not in result["data"]

    def test_lookup_case_insensitive(self):
        assert tools.get_ksi("ksi-afr-ads")["data"]["id"] == "KSI-AFR-ADS"

    def test_lookup_by_fka(self):
        # KSI-AFR-ADS has fka KSI-AFR-03 in the bundled fixture
        result = tools.get_ksi("KSI-AFR-03")
        assert result["data"]["id"] == "KSI-AFR-ADS"
        assert result["data"].get("matched_via") == "fka"

    def test_unknown_returns_error(self):
        result = tools.get_ksi("KSI-ZZZ-99")
        assert result.get("error") == "not_found"
        assert "_source" in result

    def test_response_includes_source_with_specific_path(self):
        src = tools.get_ksi("KSI-AFR-ADS")["_source"]
        assert src["json_path"] == "/KSI/AFR/indicators/KSI-AFR-ADS"


# ---------- list_frrs ----------


class TestListFrrs:
    def test_no_filter_returns_all_20x_effective(self):
        result = tools.list_frrs()
        assert result["data"]["count"] > 0
        for sec in result["data"]["sections"]:
            assert sec["effective_20x"]["is"] != "no"

    def test_filter_by_status(self):
        # All sections in the bundled snapshot are "Phase 2 Pilot" — filter should match
        result = tools.list_frrs("Phase 2 Pilot")
        assert result["data"]["status_filter"] == "Phase 2 Pilot"
        assert result["data"]["count"] > 0
        for sec in result["data"]["sections"]:
            assert sec["effective_20x"]["current_status"] == "Phase 2 Pilot"

    def test_status_filter_case_insensitive(self):
        a = tools.list_frrs("phase 2 pilot")["data"]["count"]
        b = tools.list_frrs("Phase 2 Pilot")["data"]["count"]
        assert a == b

    def test_unknown_status_returns_empty(self):
        result = tools.list_frrs("DefinitelyNotAStatus")
        assert result["data"]["count"] == 0
        assert result["data"]["sections"] == []

    def test_response_includes_source(self):
        assert tools.list_frrs()["_source"]["json_path"] == "/FRR"


# ---------- get_frr_section ----------


class TestGetFrrSection:
    def test_lookup_by_short_name(self):
        result = tools.get_frr_section("ADS")
        assert result["data"]["short_name"] == "ADS"
        assert "effective_20x" in result["data"]
        # ADS has rules in either 20x or both
        has_rules = bool(result["data"]["rules_20x_only"] or result["data"]["rules_both"])
        assert has_rules

    def test_lookup_case_insensitive(self):
        assert tools.get_frr_section("ads")["data"]["short_name"] == "ADS"

    def test_unknown_section_returns_error(self):
        result = tools.get_frr_section("ZZZ")
        assert result.get("error") == "not_found"
        assert "available_sections" in result
        assert "ADS" in result["available_sections"]

    def test_response_includes_source(self):
        src = tools.get_frr_section("ADS")["_source"]
        assert src["json_path"] == "/FRR/ADS"


# ---------- search ----------


class TestSearch:
    def test_finds_results_across_scopes(self):
        result = tools.search("vulnerability")
        assert result["data"]["count"] > 0
        scopes = {h["scope"] for h in result["data"]["hits"]}
        # 'vulnerability' should turn up in FRD at minimum
        assert "FRD" in scopes

    def test_scope_filter_narrows_results(self):
        result = tools.search("vulnerability", scope="FRD")
        assert result["data"]["scope"] == "FRD"
        for hit in result["data"]["hits"]:
            assert hit["scope"] == "FRD"

    def test_scope_filter_case_insensitive(self):
        a = tools.search("vulnerability", scope="frd")["data"]["count"]
        b = tools.search("vulnerability", scope="FRD")["data"]["count"]
        assert a == b

    def test_empty_query_returns_error(self):
        result = tools.search("")
        assert result.get("error") == "empty_query"

    def test_whitespace_query_returns_error(self):
        assert tools.search("   ").get("error") == "empty_query"

    def test_invalid_scope_returns_error(self):
        result = tools.search("anything", scope="BOGUS")
        assert result.get("error") == "invalid_scope"
        assert "valid_scopes" in result

    def test_snippet_includes_match(self):
        result = tools.search("vulnerability", scope="FRD")
        assert result["data"]["count"] > 0
        for hit in result["data"]["hits"]:
            assert "vulnerability" in hit["snippet"].lower()

    def test_no_matches_returns_empty_hits(self):
        result = tools.search("zzzzz-definitely-not-in-frmr-zzzzz")
        assert result["data"]["count"] == 0
        assert result["data"]["hits"] == []

    def test_response_includes_source(self):
        assert tools.search("vulnerability")["_source"]["json_path"] == "/"
