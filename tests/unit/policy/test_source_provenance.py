"""Provenance of material constants against verified authoritative sources (TGPS-P1-001 §20).

Each assertion names the specific authoritative document that establishes the constant, so a
later rule change cannot silently lose or weaken its legal basis.
"""

import pytest

from tax_gps.policy import rule_ids
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, load_bundled_rule_pack
from tax_gps.policy.models import RulePack, SourceAuthority, TaxRule


@pytest.fixture(scope="module")
def pack() -> RulePack:
    return load_bundled_rule_pack(BUNDLED_PACK_ID_2026)


def _rule(pack: RulePack, rule_id: str) -> TaxRule:
    return pack.rule(rule_id)


def _citations(pack: RulePack, rule_id: str) -> set[str]:
    rule = _rule(pack, rule_id)
    citations = set(rule.supplementary_source_ids)
    if rule.source_id is not None:
        citations.add(rule.source_id)
    return citations


def test_first_150000_exemption_cites_the_royal_decree_that_grants_it(pack: RulePack) -> None:
    # The Revenue Code rate schedule starts at 300,000 and does NOT itself grant the
    # 0-150,000 exemption; Royal Decree (No. 470) B.E. 2551 does.
    assert "RD-DECREE-470" in _citations(pack, rule_ids.PIT_RATE_SCHEDULE)
    source = pack.find_source("RD-DECREE-470")
    assert source is not None
    assert source.authority is SourceAuthority.THAI_LAW_ROYAL_GAZETTE


def test_bracket_schedule_cites_the_published_bracket_table(pack: RulePack) -> None:
    assert "RD-PIT-BRACKET-TABLE" in _citations(pack, rule_ids.PIT_RATE_SCHEDULE)


@pytest.mark.parametrize(
    "rule_id",
    [
        rule_ids.PERSONAL_ALLOWANCE,
        rule_ids.PARENT_ALLOWANCE,
        rule_ids.CHILD_ALLOWANCE,
        rule_ids.MORTGAGE_INTEREST,
        rule_ids.RETIREMENT_SHARED_LIMIT,
        rule_ids.SOCIAL_SECURITY_SECTION_33,
    ],
)
def test_allowance_constants_cite_the_published_deduction_schedule(
    pack: RulePack, rule_id: str
) -> None:
    assert "RD-DEDUCTION-SCHEDULE" in _citations(pack, rule_id)


def test_every_material_rule_has_at_least_one_verified_citation(pack: RulePack) -> None:
    for rule in pack.rules:
        assert _citations(pack, rule.rule_id), rule.rule_id


def test_no_source_is_orphaned(pack: RulePack) -> None:
    cited = {source_id for rule in pack.rules for source_id in _citations(pack, rule.rule_id)}
    declared = {source.source_id for source in pack.sources}
    assert declared == cited
