"""Explicit current-coverage facts for legacy scenarios (C02A-AC01)."""

from typing import Any

from tax_gps.core.money import Money
from tax_gps.profile.models import ExistingTaxBenefits
from tax_gps.profile.pvd import FundHistoryFacts, OtherRightsFacts, PvdFacts


def complete_benefits(**kwargs: Any) -> ExistingTaxBenefits:
    return ExistingTaxBenefits(
        pvd=PvdFacts(employee_paid=Money.zero()),
        other_rights=OtherRightsFacts(
            False, False, False, False, False, False, False, False, False, False
        ),
        fund_history=FundHistoryFacts(False, False, False, False),
        **kwargs,
    )
