"""C04A-AC10: versioned Thai ESG what-if export and deterministic replay."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from tax_gps.audit import AuditReplayError
from tax_gps.calculation.annual_estimate import AnnualEstimateInput
from tax_gps.calculation.annual_estimate_audit import create_annual_estimate_snapshot
from tax_gps.candidate.thai_esg_what_if import ThaiEsgWhatIfResult, WhatIfStatus
from tax_gps.candidate.thai_esg_what_if_audit import (
    SCHEMA,
    create_thai_esg_what_if_snapshot,
    replay_thai_esg_what_if,
    thai_esg_what_if_outputs,
)
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialProfile,
    ProtectionProfile,
)
from tests.acceptance.test_c03_annual_estimate import base_input, pvd_input
from tests.acceptance.test_c04a_thai_esg_what_if import HEALTHY, SHORT
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack


def policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


DEFAULT_AMOUNT = Money.of(100000)


def snapshot(
    amount: Money = DEFAULT_AMOUNT,
    financial: FinancialProfile = HEALTHY,
    estimate: AnnualEstimateInput | None = None,
) -> dict[str, Any]:
    return create_thai_esg_what_if_snapshot(
        base_input() if estimate is None else estimate,
        amount,
        financial,
        production_pack(),
        production_catalog(),
        policy(),
    ).to_dict()


def replay(payload: dict[str, Any]) -> ThaiEsgWhatIfResult:
    return replay_thai_esg_what_if(payload, production_pack(), production_catalog(), policy())


RICH = FinancialProfile(
    liquid_assets=Money.of(900000),
    monthly_essential_expenses=Money.of(30000),
    debts=(
        Debt(
            "home", DebtCategory.MORTGAGE, Money.of(1000000), Decimal("0.05"), Money.of(9000), True
        ),
    ),
    committed_cash_needs=(
        CommittedCashNeed("school", Money.of(50000), date(2027, 5, 1), True, "fees"),
    ),
    protection=ProtectionProfile(Money.of(2000000), Money.of(500000)),
)


@pytest.mark.parametrize(
    ("estimate", "financial"),
    [(None, HEALTHY), (None, SHORT), (None, RICH), ("pvd", HEALTHY)],
)
def test_c04a_snapshot_round_trips_through_replay(estimate: str | None, financial: Any) -> None:
    """C04A-AC10: replay recomputes the same outputs from material and versions."""
    request = pvd_input() if estimate == "pvd" else base_input()
    payload = snapshot(financial=financial, estimate=request)
    assert payload["schema"] == SCHEMA
    assert payload["annual_estimate"] == (
        create_annual_estimate_snapshot(request, production_pack()).to_dict()
    )
    assert payload["catalog"]["content_hash"] == production_catalog().content_hash
    assert payload["financial_policy"]["content_hash"] == policy().content_hash
    assert payload["material"]["amount"] == "100000.00"
    result = replay(payload)
    assert result.status is WhatIfStatus.READY
    assert thai_esg_what_if_outputs(result) == payload["outputs"]


def test_c04a_snapshot_outputs_carry_before_after_and_conditions() -> None:
    """C04A display/export: before/after, capacity basis, guardrail and catalog conditions."""
    outputs = snapshot()["outputs"]
    assert outputs["status"] == "READY"
    assert outputs["capacity"]["remaining_capacity"] == "297150.00"
    assert outputs["capacity_basis"] == "ASSESSABLE_INCOME"
    assert outputs["impact"]["pit_before"] == "81100.00"
    assert outputs["impact"]["pit_after"] == "62075.00"
    assert outputs["impact"]["saving"] == "19025.00"
    assert outputs["settlement_after_kind"] == "REFUND"
    assert outputs["settlement_after_amount"] == "12925.00"
    assert outputs["guardrail"]["decision"] == "ALLOW"
    assert outputs["lockup"] == {
        "minimum_holding_years": 5,
        "measurement": "purchase-date-to-purchase-date",
    }
    assert [item["evidence_id"] for item in outputs["evidence_requirements"]] == ["FUND-PURCHASE"]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("material", "amount"), "100001.00"),
        (("material", "financial", "liquid_assets"), "900000.00"),
        (("annual_estimate", "material", "forecast", "bonus"), "50001.00"),
        (("outputs", "impact", "saving"), "1.00"),
    ],
)
def test_c04a_replay_rejects_edited_payload_with_old_hash(
    path: tuple[str, ...], value: str
) -> None:
    """C04A-AC10: an edited payload keeping the old hash is rejected."""
    payload = snapshot()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(AuditReplayError, match="does not match replay"):
        replay(payload)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema", "tax-gps-thai-esg-what-if/0"),
        ("engine_version", "old"),
        ("catalog", {"catalog_id": "x", "version": "0", "content_hash": "0"}),
        ("financial_policy", {"policy_id": "x", "version": "0", "content_hash": "0"}),
    ],
)
def test_c04a_replay_rejects_version_mismatch(key: str, value: object) -> None:
    payload = snapshot()
    payload[key] = value
    with pytest.raises(AuditReplayError, match="version"):
        replay(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("material", "financial"), None),
        (("material", "financial"), "not-a-record"),
        (("material", "financial", "debts"), "not-an-array"),
        (("material", "amount"), "abc"),
    ],
)
def test_c04a_replay_rejects_malformed_material(path: tuple[str, ...], value: object) -> None:
    payload = snapshot(financial=RICH)
    target = payload
    for key in path[:-1]:
        target = target[key]
    if value is None:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    with pytest.raises(AuditReplayError, match="invalid"):
        replay(payload)


@pytest.mark.parametrize(
    ("amount", "financial", "estimate"),
    [
        (Money.of("297150.01"), HEALTHY, None),
        (Money.of(100000), FinancialProfile(), None),
        (Money.of(100000), HEALTHY, "blocked"),
    ],
)
def test_c04a_not_ready_what_if_has_no_snapshot(
    amount: Money, financial: FinancialProfile, estimate: str | None
) -> None:
    """C04A-AC06/10: only a READY what-if may be exported."""
    request = replace(base_input(), cutoff_date=None) if estimate == "blocked" else base_input()
    with pytest.raises(AuditReplayError, match="not ready"):
        snapshot(amount=amount, financial=financial, estimate=request)
