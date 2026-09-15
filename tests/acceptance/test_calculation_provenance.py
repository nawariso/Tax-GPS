"""Calculation-level provenance hardening for TGPS-P1-001B."""

import pytest

from tax_gps.audit import create_audit_snapshot, replay
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import ENGINE_VERSION, calculate_tax
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, UserProfile
from tests.support.policy import production_pack


def _profile() -> UserProfile:
    return UserProfile(
        profile_id="provenance",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(990_500)),
        benefits=ExistingTaxBenefits(social_security_paid=Money.of(10_500)),
    )


def _source_ids() -> tuple[str, ...]:
    state = calculate_tax(_profile(), production_pack())
    return tuple(source.source_id for source in state.sources)


def test_prov_01_pit_exposes_primary_and_supplementary_legal_sources() -> None:
    source_ids = _source_ids()

    assert "RD-PIT-RATES" in source_ids
    assert "RD-DECREE-470" in source_ids
    assert "RD-PIT-BRACKET-TABLE" in source_ids
    assert "RD-RC-SECTION-38-64" in source_ids


def test_prov_02_sources_are_deduplicated_in_first_reference_order() -> None:
    source_ids = _source_ids()

    assert len(source_ids) == len(set(source_ids))
    assert source_ids == (
        "RD-EXPENSE-40-1-2026",
        "RD-RC-SECTION-38-64",
        "RD-DEDUCTION-SCHEDULE",
        "OCS-SSO-WAGE-BASE-2025",
        "THGOV-CABINET-SSO-2025",
        "RD-MORTGAGE-2025-INSTRUCTIONS",
        "RD-PIT-RATES",
        "RD-DECREE-470",
        "RD-PIT-BRACKET-TABLE",
    )


@pytest.mark.replay
def test_prov_03_source_order_is_stable_across_calculations_and_replay() -> None:
    profile = _profile()
    pack = production_pack()
    first = calculate_tax(profile, pack)
    second = calculate_tax(profile, pack)
    snapshot = create_audit_snapshot(profile, first, pack)
    replayed = replay(snapshot, profile, pack)

    assert first.sources == second.sources == replayed.sources
    assert first.output_hash == second.output_hash == replayed.output_hash


def test_prov_04_sources_unrelated_to_applied_rules_are_excluded() -> None:
    source_ids = _source_ids()

    assert "RD-RMF-FAQ" not in source_ids


def test_engine_version_identifies_material_provenance_contract() -> None:
    assert ENGINE_VERSION == "tax-gps-core/0.1.1"
