"""Artifact rotation preserves history without granting current allocation authority."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.audit import AuditReplayError, create_audit_snapshot, replay
from tax_gps.candidate.activation import bundled_allocation_policy
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.engine import calculate_tax
from tax_gps.opportunity.activation import activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import load_bundled_rule_pack, rule_pack_content_hash
from tests.acceptance.test_baseline_integrity import _profile


def test_current_evidence_rotates_without_overwriting_historical_bundles() -> None:
    old = load_bundled_rule_pack(version="1.0.0")
    current = load_bundled_rule_pack()
    assert current.version == "1.0.1"
    assert old.version == "1.0.0"
    assert rule_pack_content_hash(old) == "a9e0f7d8293b3dae055206c3cce9bad2cc04320a199bd8b984c23ccd605bdf50"
    assert current.rule("TH-PIT-ALLOWANCE-SSO-33").parameters == old.rule("TH-PIT-ALLOWANCE-SSO-33").parameters
    source = current.find_source("OCS-SSO-WAGE-BASE-2025")
    assert source is not None
    assert source.url == "https://ratchakitcha.soc.go.th/documents/98728.pdf"
    assert load_bundled_rule_pack(version="1.0.0", expected_hash=rule_pack_content_hash(old)) == old


def test_current_catalog_evidence_covers_the_2026_pool_and_old_catalog_stays_historical() -> None:
    current = load_bundled_catalog()
    old = load_bundled_catalog(version="1.0.0")
    assert current.version == "1.0.1"
    assert old.version == "1.0.0"
    source = current.find_source("SEC-THAI-ESG-2026")
    assert source is not None
    assert source.published_at is None  # Footer revision date does not prove posting date.
    assert "QA-LTF-to-Thai" in source.url
    old_source = old.find_source("SEC-THAI-ESG-2026")
    assert old_source is not None
    assert old_source.published_at == date(2025, 11, 18)
    active_old = activate_catalog(old)
    assert load_bundled_catalog(version="1.0.0", expected_hash=active_old.content_hash) == old
    profile = _profile()
    pack = activate_rule_pack(load_bundled_rule_pack())
    tax = calculate_tax(profile, pack)
    discovery = discover_opportunities(profile, tax, pack, active_old,
                                      DiscoveryContext(TaxYear(2026), date(2026, 10, 15)))
    with pytest.raises(ValueError, match="bundled catalog"):
        bundled_allocation_policy(profile, tax, discovery, active_old)


@pytest.mark.parametrize("version", ["../1.0.0", "unavailable"])
def test_unrecognized_artifact_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValueError, match="version"):
        load_bundled_rule_pack(version=version)
    with pytest.raises(ValueError, match="version"):
        load_bundled_catalog(version=version)


def test_artifact_hash_mismatch_is_not_treated_as_history() -> None:
    with pytest.raises(ValueError, match="hash"):
        load_bundled_rule_pack(expected_hash="0" * 64)
    with pytest.raises(ValueError, match="hash"):
        load_bundled_catalog(expected_hash="0" * 64)


def test_current_engine_cannot_impersonate_historical_engine_for_replay() -> None:
    profile = _profile()
    pack = activate_rule_pack(load_bundled_rule_pack())
    state = calculate_tax(profile, pack)
    snapshot = create_audit_snapshot(profile, state, pack)
    old_label = replace(snapshot, engine_version="tax-gps-core/0.1.1")
    with pytest.raises(AuditReplayError, match="engine version"):
        replay(old_label, profile, pack)
    with pytest.raises(AuditReplayError, match="engine version"):
        replay(old_label, profile, pack, engine_version="tax-gps-core/0.1.1")
    with pytest.raises(ValueError, match="engine version"):
        calculate_tax(profile, pack, engine_version="tax-gps-core/0.1.1")
    assert replay(snapshot, profile, pack).pit == Money.of(79000)
