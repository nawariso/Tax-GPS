"""C02B AC08–09: authoritative baseline-only and dated replay."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.audit import AuditReplayError, create_audit_snapshot, replay
from tax_gps.calculation.availability import PlanningAvailability
from tax_gps.candidate.activation import bundled_allocation_policy
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveryStatus
from tax_gps.engine import calculate_tax
from tax_gps.opportunity.activation import catalog_to_dict
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.policy.loader import load_bundled_rule_pack, rule_pack_content_hash
from tests.acceptance.test_c02b_rmf import rmf_profile
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def test_c02b_all_consumers_are_baseline_only() -> None:
    p = rmf_profile()
    pack = production_pack()
    s = calculate_tax(p, pack)
    cat = production_catalog()
    assert s.rmf is not None
    assert s.rmf_conditions is not None
    d = discover_opportunities(p, s, pack, cat, DiscoveryContext(p.tax_year, date(2026, 10, 22)))
    assert s.planning_availability.value == "RMF_BASELINE_ONLY"
    assert [r.value for r in d.reason_codes] == ["RMF_BASELINE_ONLY"]
    assert d.opportunities == ()
    assert any(
        r.right_id == "RMF_OWN_2026" and r.claimed_amount == s.rmf.claimed
        for r in d.existing_rights
    )
    with pytest.raises(ValueError, match=r"unavailable|accepted|match"):
        s.tax_impact(Money.of(1))
    snapshot = create_audit_snapshot(p, s, pack)
    assert replay(snapshot, p, pack).material_dict() == s.material_dict()
    with pytest.raises(AuditReplayError):
        replay(replace(snapshot, engine_version="tax-gps-core/0.3.0"), p, pack)
    with pytest.raises(ValueError, match=r"unavailable|accepted|match"):
        bundled_allocation_policy(p, s, replace(d, status=DiscoveryStatus.READY), cat)
    with pytest.raises(ValueError, match=r"unavailable|accepted|match"):
        replace(s, planning_availability=PlanningAvailability.AVAILABLE).tax_impact(Money.of(1))
    with pytest.raises(ValueError, match=r"unavailable|accepted|match"):
        discover_opportunities(
            p,
            replace(s, rmf_conditions=replace(s.rmf_conditions, minimum_holding_years=0)),
            pack,
            cat,
            DiscoveryContext(p.tax_year, date(2026, 10, 22)),
        )


def test_c02b_context_date_mismatch_rejected() -> None:
    p = rmf_profile()
    pack = production_pack()
    s = calculate_tax(p, pack)
    with pytest.raises(ValueError, match="date"):
        discover_opportunities(
            p, s, pack, production_catalog(), DiscoveryContext(p.tax_year, date(2026, 10, 23))
        )


def test_c02b_explicit_historical_version_hash_load() -> None:
    pack = load_bundled_rule_pack(version="1.1.0")
    assert (
        load_bundled_rule_pack(version="1.1.0", expected_hash=rule_pack_content_hash(pack)) == pack
    )
    cat = load_bundled_catalog(version="1.1.0")
    assert (
        load_bundled_catalog(
            version="1.1.0", expected_hash=sha256_hex(canonical_json(catalog_to_dict(cat)))
        )
        == cat
    )
