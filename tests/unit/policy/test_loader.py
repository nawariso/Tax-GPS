"""Unit tests for structural Rule Pack parsing (TGPS-P1-001 §3.2)."""

import json
from datetime import date

import pytest

from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.loader import (
    BUNDLED_PACK_ID_2026,
    PolicyValidationError,
    load_bundled_rule_pack,
    parse_rule_pack,
    rule_pack_content_hash,
    rule_pack_to_dict,
)
from tax_gps.policy.models import RuleStatus, SourceAuthority
from tests.support.policy import bundled_pack_dict, rule_dict


def test_bundled_pack_parses() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    assert pack.rule_pack_id == BUNDLED_PACK_ID_2026
    assert pack.tax_year == TaxYear(2026)
    assert pack.status is RuleStatus.EFFECTIVE
    assert pack.currency == "THB"
    assert pack.rules
    assert pack.sources


def test_every_bundled_rule_carries_required_governance_metadata() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    for rule in pack.rules:
        assert rule.rule_id
        assert rule.version
        assert rule.tax_year == TaxYear(2026)
        assert isinstance(rule.effective_from, date)
        assert rule.status is RuleStatus.EFFECTIVE
        assert rule.source_id
        assert isinstance(rule.verified_at, date)


def test_every_bundled_source_is_official_https() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    for source in pack.sources:
        assert source.url.startswith("https://")
        assert source.authority in SourceAuthority
        assert source.title
        assert source.publisher


def test_rule_lookup() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    first = pack.rules[0]
    assert pack.rule(first.rule_id) is first
    assert pack.find_rule("NOT-A-RULE") is None
    with pytest.raises(KeyError):
        pack.rule("NOT-A-RULE")


def test_source_lookup() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    first = pack.sources[0]
    assert pack.find_source(first.source_id) is first
    assert pack.find_source("NOT-A-SOURCE") is None


def test_round_trip_to_dict_is_lossless() -> None:
    original = bundled_pack_dict()
    parsed = parse_rule_pack(json.dumps(original))
    assert rule_pack_to_dict(parsed) == original


def test_content_hash_is_stable_and_sensitive_to_content() -> None:
    original = bundled_pack_dict()
    first = rule_pack_content_hash(parse_rule_pack(json.dumps(original)))
    reordered = parse_rule_pack(json.dumps(original, sort_keys=True, indent=4))
    assert rule_pack_content_hash(reordered) == first
    assert len(first) == 64
    original["description"] = original["description"] + " (changed)"
    assert rule_pack_content_hash(parse_rule_pack(json.dumps(original))) != first


def test_parameters_are_immutable() -> None:
    pack = load_bundled_rule_pack(BUNDLED_PACK_ID_2026)
    with pytest.raises(TypeError):
        pack.rules[0].parameters["x"] = "1"  # type: ignore[call-overload,index]


def test_unknown_bundled_pack_is_rejected() -> None:
    with pytest.raises(PolicyValidationError, match="unknown bundled rule pack"):
        load_bundled_rule_pack("TH-PIT-1999-001")


@pytest.mark.negative
class TestStructuralRejection:
    def _parse(self, data: object) -> None:
        parse_rule_pack(json.dumps(data))

    def test_malformed_json(self) -> None:
        with pytest.raises(PolicyValidationError, match="JSON"):
            parse_rule_pack("{not json")

    def test_float_anywhere_is_rejected(self) -> None:
        text = json.dumps(bundled_pack_dict()).replace('"schema_version": "1"', '"x": 1.5', 1)
        with pytest.raises(PolicyValidationError, match="float"):
            parse_rule_pack(text)

    def test_nan_constant_is_rejected(self) -> None:
        with pytest.raises(PolicyValidationError):
            parse_rule_pack('{"a": NaN}')

    def test_top_level_must_be_object(self) -> None:
        with pytest.raises(PolicyValidationError, match="object"):
            self._parse([1])

    def test_missing_top_level_key(self) -> None:
        data = bundled_pack_dict()
        del data["rules"]
        with pytest.raises(PolicyValidationError, match="rules"):
            self._parse(data)

    def test_unknown_top_level_key(self) -> None:
        data = bundled_pack_dict()
        data["surprise"] = "x"
        with pytest.raises(PolicyValidationError, match="surprise"):
            self._parse(data)

    def test_unsupported_schema_version(self) -> None:
        data = bundled_pack_dict()
        data["schema_version"] = "99"
        with pytest.raises(PolicyValidationError, match="schema_version"):
            self._parse(data)

    def test_unknown_status(self) -> None:
        data = bundled_pack_dict()
        data["status"] = "APPROVED-ISH"
        with pytest.raises(PolicyValidationError, match="status"):
            self._parse(data)

    def test_non_string_field(self) -> None:
        data = bundled_pack_dict()
        data["rule_pack_id"] = 7
        with pytest.raises(PolicyValidationError, match="rule_pack_id"):
            self._parse(data)

    def test_tax_year_must_be_int(self) -> None:
        data = bundled_pack_dict()
        data["tax_year"] = "2026"
        with pytest.raises(PolicyValidationError, match="tax_year"):
            self._parse(data)

    def test_rule_tax_year_must_be_int(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["tax_year"] = True
        with pytest.raises(PolicyValidationError, match="tax_year"):
            self._parse(data)

    def test_rule_tax_year_must_be_gregorian(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["tax_year"] = 2569
        with pytest.raises(PolicyValidationError, match="tax_year"):
            self._parse(data)

    def test_buddhist_tax_year_is_rejected(self) -> None:
        data = bundled_pack_dict()
        data["tax_year"] = 2569
        with pytest.raises(PolicyValidationError, match="tax_year"):
            self._parse(data)

    def test_rules_must_be_list(self) -> None:
        data = bundled_pack_dict()
        data["rules"] = {}
        with pytest.raises(PolicyValidationError, match="rules"):
            self._parse(data)

    def test_sources_must_be_list(self) -> None:
        data = bundled_pack_dict()
        data["sources"] = {}
        with pytest.raises(PolicyValidationError, match="sources"):
            self._parse(data)

    def test_rule_must_be_object(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0] = "rule"
        with pytest.raises(PolicyValidationError, match="object"):
            self._parse(data)

    def test_duplicate_rule_id(self) -> None:
        data = bundled_pack_dict()
        data["rules"].append(dict(data["rules"][0]))
        with pytest.raises(PolicyValidationError, match="duplicate rule_id"):
            self._parse(data)

    def test_duplicate_source_id(self) -> None:
        data = bundled_pack_dict()
        data["sources"].append(dict(data["sources"][0]))
        with pytest.raises(PolicyValidationError, match="duplicate source_id"):
            self._parse(data)

    def test_bad_date(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["effective_from"] = "01/01/2026"
        with pytest.raises(PolicyValidationError, match="effective_from"):
            self._parse(data)

    def test_effective_to_before_effective_from(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["effective_from"] = "2026-01-01"
        data["rules"][0]["effective_to"] = "2025-12-31"
        with pytest.raises(PolicyValidationError, match="effective_to"):
            self._parse(data)

    def test_unknown_source_authority(self) -> None:
        data = bundled_pack_dict()
        data["sources"][0]["authority"] = "BLOG"
        with pytest.raises(PolicyValidationError, match="authority"):
            self._parse(data)

    def test_unknown_rule_key(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["maybe"] = True
        with pytest.raises(PolicyValidationError, match="maybe"):
            self._parse(data)

    def test_parameters_must_be_object(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["parameters"] = []
        with pytest.raises(PolicyValidationError, match="parameters"):
            self._parse(data)

    def test_string_list_fields_must_hold_strings(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["supplementary_source_ids"] = [1]
        with pytest.raises(PolicyValidationError, match="supplementary_source_ids"):
            self._parse(data)

    def test_string_list_field_must_be_list(self) -> None:
        data = bundled_pack_dict()
        data["rules"][0]["review_notes"] = "note"
        with pytest.raises(PolicyValidationError, match="review_notes"):
            self._parse(data)

    def test_nullable_source_id_is_structurally_allowed(self) -> None:
        # Missing provenance is a governance failure detected at activation (POLICY-02),
        # not a JSON-structure failure, so it must parse.
        data = bundled_pack_dict()
        rule = rule_dict(data, data["rules"][0]["rule_id"])
        rule["source_id"] = None
        rule["verified_at"] = None
        pack = parse_rule_pack(json.dumps(data))
        assert pack.rules[0].source_id is None
        assert pack.rules[0].verified_at is None
