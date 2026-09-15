"""Policy Readiness and activation (TGPS-P1-001 §§3.2/14, DMN Policy Readiness)."""

import json

import pytest

from tax_gps.policy import rule_ids
from tax_gps.policy.activation import PolicyActivationError, activate_rule_pack
from tax_gps.policy.loader import parse_rule_pack
from tax_gps.policy.readiness import (
    REQUIRED_RULE_IDS,
    ReadinessCode,
    evaluate_policy_readiness,
)
from tests.support.policy import (
    PackDict,
    activate_dict,
    bundled_pack_dict,
    rule_dict,
    source_dict,
)


def _codes(pack: PackDict) -> set[ReadinessCode]:
    readiness = evaluate_policy_readiness(parse_rule_pack(json.dumps(pack)))
    return {finding.code for finding in readiness.findings}


def _assert_activation_fails(pack: PackDict, code: ReadinessCode) -> None:
    with pytest.raises(PolicyActivationError) as info:
        activate_dict(pack)
    assert code in {finding.code for finding in info.value.findings}
    assert code.value in str(info.value)


def test_bundled_pack_is_ready() -> None:
    readiness = evaluate_policy_readiness(parse_rule_pack(json.dumps(bundled_pack_dict())))
    assert readiness.ready, readiness.findings
    assert readiness.findings == ()


def test_required_rules_cover_every_material_rule_the_engine_uses() -> None:
    assert set(REQUIRED_RULE_IDS) == set(rule_ids.ALL_RULE_IDS)


def test_activation_exposes_typed_rules() -> None:
    activated = activate_dict(bundled_pack_dict())
    assert activated.rule_pack_id == bundled_pack_dict()["rule_pack_id"]
    assert activated.version == bundled_pack_dict()["version"]
    assert len(activated.content_hash) == 64


@pytest.mark.mandatory
@pytest.mark.negative
def test_policy_01_draft_pack_is_blocked() -> None:
    pack = bundled_pack_dict()
    pack["status"] = "DRAFT"
    assert ReadinessCode.PACK_NOT_EFFECTIVE in _codes(pack)
    _assert_activation_fails(pack, ReadinessCode.PACK_NOT_EFFECTIVE)


@pytest.mark.negative
@pytest.mark.parametrize("status", ["DRAFT", "VERIFIED", "SUPERSEDED", "EXPIRED"])
def test_non_effective_pack_status_is_blocked(status: str) -> None:
    pack = bundled_pack_dict()
    pack["status"] = status
    _assert_activation_fails(pack, ReadinessCode.PACK_NOT_EFFECTIVE)


@pytest.mark.negative
@pytest.mark.parametrize("status", ["DRAFT", "VERIFIED", "SUPERSEDED", "EXPIRED"])
def test_non_effective_rule_status_is_blocked(status: str) -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PIT_RATE_SCHEDULE)["status"] = status
    _assert_activation_fails(pack, ReadinessCode.RULE_NOT_EFFECTIVE)


@pytest.mark.mandatory
@pytest.mark.negative
def test_policy_02_rule_without_source_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PIT_RATE_SCHEDULE)["source_id"] = None
    _assert_activation_fails(pack, ReadinessCode.RULE_SOURCE_MISSING)


@pytest.mark.negative
def test_policy_02_rule_with_blank_source_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"] = "  "
    _assert_activation_fails(pack, ReadinessCode.RULE_SOURCE_MISSING)


@pytest.mark.negative
def test_policy_02_rule_with_dangling_source_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"] = "SRC-DOES-NOT-EXIST"
    _assert_activation_fails(pack, ReadinessCode.RULE_SOURCE_UNRESOLVED)


@pytest.mark.negative
def test_dangling_supplementary_source_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["supplementary_source_ids"] = ["SRC-NOPE"]
    _assert_activation_fails(pack, ReadinessCode.RULE_SOURCE_UNRESOLVED)


@pytest.mark.negative
def test_source_without_https_url_fails_activation() -> None:
    pack = bundled_pack_dict()
    source_id = rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"]
    source_dict(pack, source_id)["url"] = "http://www.rd.go.th/"
    _assert_activation_fails(pack, ReadinessCode.SOURCE_NOT_AUTHORITATIVE)


@pytest.mark.negative
def test_government_authority_on_non_government_host_fails_activation() -> None:
    pack = bundled_pack_dict()
    source_id = rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"]
    source_dict(pack, source_id)["url"] = "https://some-tax-blog.example.com/allowances"
    _assert_activation_fails(pack, ReadinessCode.SOURCE_NOT_AUTHORITATIVE)


@pytest.mark.negative
def test_lookalike_government_host_fails_activation() -> None:
    pack = bundled_pack_dict()
    source_id = rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"]
    source_dict(pack, source_id)["url"] = "https://rd.go.th.example.com/x"
    _assert_activation_fails(pack, ReadinessCode.SOURCE_NOT_AUTHORITATIVE)


def test_official_provider_may_use_non_government_https_host() -> None:
    pack = bundled_pack_dict()
    source_id = rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"]
    source = source_dict(pack, source_id)
    source["authority"] = "OFFICIAL_PROVIDER"
    source["url"] = "https://provider.example.com/official"
    assert ReadinessCode.SOURCE_NOT_AUTHORITATIVE not in _codes(pack)


@pytest.mark.negative
def test_unverified_rule_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["verified_at"] = None
    _assert_activation_fails(pack, ReadinessCode.RULE_NOT_VERIFIED)


@pytest.mark.negative
def test_missing_required_rule_fails_activation() -> None:
    pack = bundled_pack_dict()
    pack["rules"] = [r for r in pack["rules"] if r["rule_id"] != rule_ids.MORTGAGE_INTEREST]
    _assert_activation_fails(pack, ReadinessCode.REQUIRED_RULE_MISSING)


@pytest.mark.negative
def test_rule_for_other_tax_year_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["tax_year"] = 2025
    _assert_activation_fails(pack, ReadinessCode.RULE_TAX_YEAR_MISMATCH)


@pytest.mark.negative
def test_rule_starting_mid_year_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["effective_from"] = "2026-07-01"
    _assert_activation_fails(pack, ReadinessCode.RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR)


@pytest.mark.negative
def test_rule_ending_mid_year_fails_activation() -> None:
    pack = bundled_pack_dict()
    rule = rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)
    rule["effective_to"] = "2026-06-30"
    _assert_activation_fails(pack, ReadinessCode.RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR)


def test_rule_ending_on_last_day_of_tax_year_is_ready() -> None:
    pack = bundled_pack_dict()
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["effective_to"] = "2026-12-31"
    assert _codes(pack) == set()


@pytest.mark.negative
def test_unsupported_currency_fails_activation() -> None:
    pack = bundled_pack_dict()
    pack["currency"] = "USD"
    _assert_activation_fails(pack, ReadinessCode.PACK_CURRENCY_UNSUPPORTED)


@pytest.mark.negative
def test_unsupported_jurisdiction_fails_activation() -> None:
    pack = bundled_pack_dict()
    pack["jurisdiction"] = "SG"
    _assert_activation_fails(pack, ReadinessCode.PACK_JURISDICTION_UNSUPPORTED)


@pytest.mark.negative
def test_multiple_findings_are_all_reported() -> None:
    pack = bundled_pack_dict()
    pack["status"] = "DRAFT"
    rule_dict(pack, rule_ids.PERSONAL_ALLOWANCE)["source_id"] = None
    assert {ReadinessCode.PACK_NOT_EFFECTIVE, ReadinessCode.RULE_SOURCE_MISSING} <= _codes(pack)


def test_activation_accepts_parsed_pack_directly() -> None:
    activated = activate_rule_pack(parse_rule_pack(json.dumps(bundled_pack_dict())))
    assert activated.pack.rule_pack_id == activated.rule_pack_id
