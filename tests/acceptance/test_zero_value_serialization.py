"""Zero-valued material amounts must serialize as amounts, never as null.

G01 produces a zero PIT on a fully supported calculation. If a zero amount ever collapsed to
``null`` in the canonical material output it would be indistinguishable from the unsupported
state, and the audit hash would silently change meaning. These tests pin that contract.
"""

from dataclasses import replace

import pytest

from tax_gps.calculation.models import TaxStatus
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.profile.models import (
    ExistingTaxBenefits,
    IncomeProfile,
    UnsupportedIncome,
    UserProfile,
)
from tests.support.policy import production_pack


def _profile(salary: int) -> UserProfile:
    return UserProfile(
        profile_id="zero-value",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(section_40_1=Money.of(salary)),
        benefits=ExistingTaxBenefits(social_security_paid=Money.of(10500)),
    )


@pytest.mark.replay
def test_zero_pit_serializes_as_zero_not_null() -> None:
    state = calculate_tax(_profile(300000), production_pack())
    assert state.status is TaxStatus.READY
    assert state.pit == Money.zero()
    data = state.material_dict()
    assert data["pit"] == "0.00"
    assert data["marginal_rate"] == "0"
    assert data["taxable_income"] == "129500.00"


@pytest.mark.replay
def test_zero_taxable_income_serializes_as_zero_not_null() -> None:
    state = calculate_tax(_profile(0), production_pack())
    data = state.material_dict()
    assert data["taxable_income"] == "0.00"
    assert data["pit"] == "0.00"


@pytest.mark.replay
def test_unsupported_state_is_the_only_source_of_null_amounts() -> None:
    user = replace(
        _profile(300000),
        income=IncomeProfile(
            section_40_1=Money.of(300000),
            unsupported=(UnsupportedIncome("40(8)", Money.of(1)),),
        ),
    )
    data = calculate_tax(user, production_pack()).material_dict()
    assert data["taxable_income"] is None
    assert data["pit"] is None
    assert data["marginal_rate"] is None


@pytest.mark.replay
def test_zero_pit_and_unsupported_state_have_different_hashes() -> None:
    zero_pit = calculate_tax(_profile(300000), production_pack())
    unsupported = calculate_tax(
        replace(
            _profile(300000),
            income=IncomeProfile(
                section_40_1=Money.of(300000),
                unsupported=(UnsupportedIncome("40(8)", Money.of(1)),),
            ),
        ),
        production_pack(),
    )
    assert zero_pit.output_hash != unsupported.output_hash
