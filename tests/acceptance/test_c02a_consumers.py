"""C02A-AC06..08: baseline availability and consumer authority."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.audit import AuditReplayError, create_audit_snapshot, replay
from tax_gps.candidate.activation import activate_allocation_policy, bundled_allocation_policy
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.discovery.models import DiscoveryStatus
from tax_gps.engine import calculate_tax
from tax_gps.policy.loader import load_bundled_rule_pack
from tests.acceptance.test_c02a_pvd import normal_profile
from tests.acceptance.test_candidates import _inputs
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def test_c02a_positive_pvd_baseline_only_all_consumers() -> None:
    user = normal_profile()
    pack = production_pack()
    state = calculate_tax(user, pack)
    assert state.status.value == "READY"
    assert state.planning_availability.value == "PVD_BASELINE_ONLY"
    with pytest.raises(ValueError, match="unavailable"):
        state.tax_impact(Money.of(1))
    discovery = discover_opportunities(
        user, state, pack, production_catalog(), DiscoveryContext(user.tax_year, date(2026, 10, 22))
    )
    assert discovery.baseline_status == "READY"
    assert discovery.status.value == "UNSUPPORTED"
    assert not discovery.opportunities
    assert [r.value for r in discovery.reason_codes] == ["PVD_BASELINE_ONLY"]
    assert any(r.right_id == "TH-RIGHT-PVD" for r in discovery.existing_rights)


def test_c02a_zero_retains_candidates() -> None:
    state = calculate_tax(normal_profile("0"), production_pack())
    assert state.planning_availability.value == "AVAILABLE"
    assert state.tax_impact(Money.of(1)).saving == Money.zero()


def test_c02a_replay_material_and_hash() -> None:
    user = normal_profile()
    pack = production_pack()
    state = calculate_tax(user, pack)
    snapshot = create_audit_snapshot(user, state, pack)
    assert replay(snapshot, user, pack).material_dict() == state.material_dict()
    with pytest.raises(AuditReplayError):
        replay(replace(snapshot, engine_version="tax-gps-core/0.2.0"), user, pack)


def test_c02a_historical_bytes_and_current_rejection() -> None:
    assert load_bundled_rule_pack().version == "1.2.0"
    assert load_bundled_rule_pack(version="1.0.1").version == "1.0.1"


def test_c02a_forged_ready_discovery_cannot_activate() -> None:
    user = normal_profile()
    pack = production_pack()
    catalog = production_catalog()
    state = calculate_tax(user, pack)
    discovered = discover_opportunities(
        user, state, pack, catalog, DiscoveryContext(user.tax_year, date(2026, 10, 22))
    )
    forged = replace(discovered, status=DiscoveryStatus.READY, reason_codes=())
    forged = replace(forged, discovery_hash=sha256_hex(canonical_json(forged.material_dict())))
    _, _, _, _, policy = _inputs()
    with pytest.raises(ValueError, match="accepted tax/discovery"):
        activate_allocation_policy(policy, user, state, forged, catalog)
    with pytest.raises(ValueError, match="accepted tax/discovery"):
        bundled_allocation_policy(user, state, discovered, catalog)
