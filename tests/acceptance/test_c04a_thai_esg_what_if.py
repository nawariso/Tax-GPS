"""C04A-AC01–09: user-chosen Thai ESG amount on top of the C03 annual estimate."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from tax_gps.calculation.annual_estimate import (
    AnnualEstimateInput,
    SettlementKind,
    calculate_annual_estimate,
)
from tax_gps.calculation.models import TaxStatus
from tax_gps.candidate.thai_esg_what_if import (
    CapacityBasis,
    ThaiEsgWhatIfInput,
    ThaiEsgWhatIfInputError,
    ThaiEsgWhatIfResult,
    WhatIfStatus,
    evaluate_thai_esg_what_if,
)
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.models import GuardrailDecision
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tax_gps.financial.profile import CommittedCashNeed, Debt, DebtCategory, FinancialProfile
from tax_gps.financial.reason_codes import FinancialReasonCode
from tax_gps.profile.models import SharedLimitUsage
from tests.acceptance.test_c03_annual_estimate import (
    base_input,
    pvd_input,
    rmf_input,
    year_end_input,
)
from tests.support.catalog import artwork_ready_catalog, production_catalog
from tests.support.policy import production_pack

HEALTHY = FinancialProfile(
    liquid_assets=Money.of(1000000), monthly_essential_expenses=Money.of(30000)
)
SHORT = FinancialProfile(liquid_assets=Money.of(190000), monthly_essential_expenses=Money.of(30000))
BELOW_FLOOR = FinancialProfile(
    liquid_assets=Money.of(50000), monthly_essential_expenses=Money.of(30000)
)
DEFAULT_AMOUNT = Money.of(100000)


def evaluate(
    estimate: AnnualEstimateInput | None = None,
    amount: Money | None = DEFAULT_AMOUNT,
    financial: FinancialProfile = HEALTHY,
) -> ThaiEsgWhatIfResult:
    return evaluate_thai_esg_what_if(
        base_input() if estimate is None else estimate,
        ThaiEsgWhatIfInput(amount, financial),
        production_pack(),
        production_catalog(),
        activate_financial_policy(bundled_financial_policy(TaxYear(2026))),
    )


@pytest.mark.parametrize(
    ("amount", "after", "saving", "kind", "settled"),
    [
        ("0", "81100", "0", SettlementKind.PAY_MORE, "6100"),
        ("100000", "62075", "19025", SettlementKind.REFUND, "12925"),
        ("297150", "32502.50", "48597.50", SettlementKind.REFUND, "42497.50"),
    ],
)
def test_c04a_amount_impact_matches_reference(
    amount: str, after: str, saving: str, kind: SettlementKind, settled: str
) -> None:
    """C04A-AC01/02/03: ESG-0, ESG-100K, ESG-CAP from the acceptance reference."""
    result = evaluate(amount=Money.of(amount))
    assert result.status is WhatIfStatus.READY
    assert result.reason_codes == result.missing_fact_ids == ()
    assert result.capacity is not None
    assert result.capacity.remaining_capacity == Money.of("297150")
    assert result.capacity_basis is CapacityBasis.ASSESSABLE_INCOME
    assert result.impact is not None
    assert result.impact.pit_before == Money.of(81100)
    assert result.impact.pit_after == Money.of(after)
    assert result.impact.saving == Money.of(saving)
    assert result.settlement_after_kind is kind
    assert result.settlement_after_amount == Money.of(settled)
    assert result.guardrail is not None
    assert result.guardrail.decision is GuardrailDecision.ALLOW


def test_c04a_zero_amount_equals_c03_estimate() -> None:
    """C04A-AC02: amount 0 reproduces every C03 figure."""
    c03 = calculate_annual_estimate(base_input(), production_pack())
    result = evaluate(amount=Money.zero())
    assert result.estimate == c03
    assert result.impact is not None
    assert c03.tax is not None
    assert result.impact.pit_after == c03.tax.pit
    assert result.settlement_after_kind is c03.settlement_kind
    assert result.settlement_after_amount == c03.settlement_amount


def test_c04a_capacity_boundary_is_not_computed_above_limit() -> None:
    """C04A-AC03 / D4: 0.01 above the tax capacity is not computed; the limit is shown."""
    result = evaluate(amount=Money.of("297150.01"))
    assert result.status is WhatIfStatus.EXCEEDS_TAX_CAPACITY
    assert result.reason_codes == ("THAI_ESG_AMOUNT_EXCEEDS_TAX_CAPACITY",)
    assert result.capacity is not None
    assert result.capacity.remaining_capacity == Money.of("297150")
    assert result.impact is None
    assert result.settlement_after_kind is None
    assert result.settlement_after_amount is None


def test_c04a_forecast_edit_moves_capacity_and_keeps_actuals() -> None:
    """C04A-AC04: ESG-FORECAST-EDIT; capacity crosses the 300,000 cap."""
    request = base_input()
    edited = replace(request, forecast=replace(request.forecast, bonus=Money.of(70000)))
    result = evaluate(edited)
    assert edited.actual == request.actual
    assert result.capacity is not None
    assert result.capacity.remaining_capacity == Money.of(300000)
    assert result.impact is not None
    assert result.impact.pit_before == Money.of(85100)
    assert result.impact.pit_after == Money.of(65100)
    assert result.impact.saving == Money.of(20000)


def test_c04a_withholding_missing_keeps_pit_but_nulls_settlement() -> None:
    """C04A-AC05: ESG-WHT-MISSING."""
    request = base_input()
    result = evaluate(replace(request, forecast=replace(request.forecast, withholding=None)))
    assert result.status is WhatIfStatus.READY
    assert result.estimate.settlement_status is TaxStatus.REQUIRES_INPUT
    assert result.estimate.withholding_missing_fact_ids == ("forecast.withholding",)
    assert result.impact is not None
    assert result.impact.pit_after == Money.of(62075)
    assert result.settlement_after_kind is None
    assert result.settlement_after_amount is None


@pytest.mark.parametrize(
    "change",
    [
        {"cutoff_date": None},
        {"actual_outside": True},
        {"shared": None},
        {"shared": "1"},
    ],
)
def test_c04a_blocked_baseline_hides_everything(change: dict[str, object]) -> None:
    """C04A-AC06/07: C03 not READY closes the what-if; prior usage comes from C03."""
    request = base_input()
    if "cutoff_date" in change:
        request = replace(request, cutoff_date=None)
    if "actual_outside" in change:
        request = replace(request, actual=replace(request.actual, outside_coverage=True))
    if "shared" in change:
        value = change["shared"]
        request = replace(
            request,
            shared_limit_usage=None
            if value is None
            else (SharedLimitUsage("THAI_ESG_2026_POOL", Money.of(str(value))),),
        )
    result = evaluate(request)
    assert result.estimate.tax is None
    assert result.status is WhatIfStatus.BASELINE_NOT_READY
    assert result.reason_codes == result.estimate.baseline.reason_codes
    assert result.missing_fact_ids == result.estimate.baseline.missing_fact_ids
    assert result.capacity is None
    assert result.guardrail is None
    assert result.impact is None
    assert result.financial_state is None


@pytest.mark.parametrize(
    ("amount", "financial", "missing"),
    [
        (None, HEALTHY, ("thai_esg_what_if.amount",)),
        (
            Money.of(100000),
            FinancialProfile(monthly_essential_expenses=Money.of(30000)),
            ("financial.liquid_assets",),
        ),
        (
            None,
            FinancialProfile(),
            (
                "thai_esg_what_if.amount",
                "financial.liquid_assets",
                "financial.monthly_essential_expenses",
            ),
        ),
    ],
)
def test_c04a_missing_what_if_inputs_keep_c03_visible(
    amount: Money | None, financial: FinancialProfile, missing: tuple[str, ...]
) -> None:
    """C04A-AC08: unknown is not zero; only the what-if part is closed."""
    result = evaluate(amount=amount, financial=financial)
    assert result.status is WhatIfStatus.REQUIRES_INPUT
    assert result.missing_fact_ids == missing
    assert result.estimate.tax is not None
    assert result.estimate.tax.pit == Money.of(81100)
    assert result.capacity is None
    assert result.guardrail is None
    assert result.impact is None


@pytest.mark.parametrize(
    ("financial", "amount", "status", "decision", "limit", "reason"),
    [
        (
            SHORT,
            "100000",
            WhatIfStatus.READY,
            GuardrailDecision.CAP,
            "100000",
            FinancialReasonCode.ALLOCATION_CAPPED_BY_LIQUIDITY,
        ),
        (
            SHORT,
            "100000.01",
            WhatIfStatus.GUARDRAIL_LIMITED,
            GuardrailDecision.CAP,
            "100000",
            FinancialReasonCode.ALLOCATION_CAPPED_BY_LIQUIDITY,
        ),
        (
            BELOW_FLOOR,
            "1",
            WhatIfStatus.GUARDRAIL_LIMITED,
            GuardrailDecision.BLOCK,
            "0",
            FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR,
        ),
        (
            replace(
                HEALTHY,
                debts=(
                    Debt(
                        "card",
                        DebtCategory.CREDIT_CARD,
                        Money.of(20000),
                        Decimal("0.18"),
                        Money.of(2000),
                        False,
                    ),
                ),
            ),
            "1",
            WhatIfStatus.GUARDRAIL_LIMITED,
            GuardrailDecision.BLOCK,
            "0",
            FinancialReasonCode.CRITICAL_DEBT_PRESENT,
        ),
    ],
)
def test_c04a_guardrail_limits_use_existing_decisions(  # noqa: PLR0917 - parametrized case
    financial: FinancialProfile,
    amount: str,
    status: WhatIfStatus,
    decision: GuardrailDecision,
    limit: str,
    reason: FinancialReasonCode,
) -> None:
    """C04A-AC08 / D3 / D4: reserve, liquidity and critical-debt guardrails still work."""
    result = evaluate(amount=Money.of(amount), financial=financial)
    assert result.status is status
    assert result.guardrail is not None
    assert result.guardrail.decision is decision
    assert result.guardrail.max_feasible_allocation == Money.of(limit)
    assert reason in result.guardrail.reason_codes
    assert result.estimate.tax is not None
    if status is WhatIfStatus.READY:
        assert result.impact is not None
    else:
        assert result.impact is None
        assert reason.value in result.reason_codes


def test_c04a_tax_capacity_wins_when_both_limits_are_exceeded() -> None:
    """Plan: EXCEEDS_TAX_CAPACITY is reported before the guardrail limit."""
    result = evaluate(amount=Money.of(400000), financial=BELOW_FLOOR)
    assert result.status is WhatIfStatus.EXCEEDS_TAX_CAPACITY
    assert result.guardrail is not None
    assert result.guardrail.decision is GuardrailDecision.BLOCK


def test_c04a_pvd_positive_uses_conservative_basis() -> None:
    """C04A-AC09 / D1 / D7: PVD-ESG-100K and PVD-ESG-CAP (provisional)."""
    result = evaluate(pvd_input())
    assert result.status is WhatIfStatus.READY
    assert result.capacity_basis is CapacityBasis.CONSERVATIVE_AFTER_PVD_EXEMPTION
    assert result.capacity is not None
    assert result.capacity.remaining_capacity == Money.of(291150)
    assert result.impact is not None
    assert result.impact.pit_before == Money.of(75100)
    assert result.impact.pit_after == Money.of(57575)
    assert result.settlement_after_kind is SettlementKind.REFUND
    assert result.settlement_after_amount == Money.of(17425)
    cap = evaluate(pvd_input(), amount=Money.of(291150))
    assert cap.impact is not None
    assert cap.impact.pit_after == Money.of("28902.50")
    over = evaluate(pvd_input(), amount=Money.of("291150.01"))
    assert over.status is WhatIfStatus.EXCEEDS_TAX_CAPACITY


def test_c04a_rmf_positive_is_unsupported_in_v01() -> None:
    """C04A-AC09: RMF_BASELINE_ONLY stays closed; no retirement capacity is created."""
    result = evaluate(rmf_input())
    assert result.estimate.tax is not None
    assert result.status is WhatIfStatus.UNSUPPORTED
    assert result.reason_codes == ("RMF_BASELINE_ONLY",)
    assert result.capacity is None
    assert result.guardrail is None
    assert result.impact is None


@pytest.mark.parametrize("amount", ["-0.01", "0.001"])
def test_c04a_amount_validation_names_field_without_value(amount: str) -> None:
    """C04A-AC08: invalid amount is an input error naming the field, not the value."""
    with pytest.raises(ThaiEsgWhatIfInputError) as caught:
        evaluate(amount=Money(Decimal(amount)))
    assert caught.value.fact_id == "thai_esg_what_if.amount"
    assert amount.lstrip("-") not in str(caught.value)


def test_c04a_rejects_non_bundled_catalog() -> None:
    """Production authority: only the bundled activated catalog may grant capacity."""
    with pytest.raises(ValueError, match="bundled catalog"):
        evaluate_thai_esg_what_if(
            base_input(),
            ThaiEsgWhatIfInput(Money.of(1), HEALTHY),
            production_pack(),
            artwork_ready_catalog(),
            activate_financial_policy(bundled_financial_policy(TaxYear(2026))),
        )


def test_c04a_conditions_come_from_catalog() -> None:
    """C04A display: lock-up and evidence are read from the catalog definition."""
    result = evaluate()
    definition = production_catalog().catalog.definition("TH-OPP-THAI-ESG-2026")
    assert result.lockup == definition.lockup_metadata
    assert result.evidence_requirements == definition.evidence_requirements


@pytest.mark.parametrize(
    "financial",
    [
        HEALTHY,
        replace(
            HEALTHY,
            committed_cash_needs=(
                CommittedCashNeed("fee", Money.of(50000), date(2026, 11, 1), True, "paid"),
            ),
        ),
    ],
)
def test_c04a_year_end_cutoff_uses_actual_income(financial: FinancialProfile) -> None:
    """C04A-AC01 at 31 Dec: capacity from actual income; a past-due need is not near-term cash."""
    result = evaluate(year_end_input(), financial=financial)
    assert result.status is WhatIfStatus.READY
    assert result.capacity is not None
    assert result.capacity.remaining_capacity == Money.of(297150)
    assert result.impact is not None
    assert result.impact.pit_after == Money.of(62075)
    assert result.settlement_after_kind is SettlementKind.REFUND
    assert result.settlement_after_amount == Money.of(12925)
    assert result.financial_state is not None
    assert result.financial_state.near_term_committed_cash == Money.zero()
