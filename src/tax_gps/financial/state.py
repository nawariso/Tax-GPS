"""Deterministic Financial State computation (TGPS-P1-003 §16-21, §41).

``compute_financial_state`` never reads a clock; every date-dependent calculation is driven
by the explicit ``planning_date`` on :class:`FinancialPlanningContext`. No financial fact is
inferred: liquid assets, expenses, debt APR, and protection coverage are used exactly as
supplied, and ``None`` always means "unknown", never "zero".
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, replace
from datetime import date
from decimal import ROUND_HALF_UP, Context, Decimal, DecimalException
from enum import StrEnum

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    evaluate_financial_policy_temporal_readiness,
)
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile
from tax_gps.financial.reason_codes import FinancialReasonCode

FINANCIAL_STATE_ENGINE_VERSION = "tax-gps-financial-state/0.1.0"
_RATIO_PLACES = 2
_RATIO_QUANTIZE = Decimal(1).scaleb(-_RATIO_PLACES)
_ROUNDING_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)


class FinancialStateStatus(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    POLICY_NOT_READY = "POLICY_NOT_READY"
    UNSUPPORTED = "UNSUPPORTED"


class FinancialValidationError(InvalidValueError):
    """Financial inputs fail closed rather than being silently accepted (§22, §26)."""


def _money(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


def _add_months(base: date, months: int) -> date:
    total = base.month - 1 + months
    year = base.year + total // 12
    month = total % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True, slots=True)
class FinancialState:
    status: FinancialStateStatus
    liquid_assets: Money | None
    monthly_essential_expenses: Money | None

    emergency_fund_months: str | None
    emergency_reserve_floor: Money | None
    emergency_reserve_target: Money | None

    near_term_committed_cash: Money
    protected_liquidity: Money | None
    spendable_surplus: Money | None

    critical_debt_balance: Money
    critical_debt_ids: tuple[str, ...]

    protection_gap: Money | None

    reason_codes: tuple[FinancialReasonCode, ...]

    policy_id: str
    policy_version: str
    policy_hash: str

    planning_date: date

    engine_version: str
    state_hash: str
    profile_hash: str

    def material_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "liquid_assets": _money(self.liquid_assets),
            "monthly_essential_expenses": _money(self.monthly_essential_expenses),
            "emergency_fund_months": self.emergency_fund_months,
            "emergency_reserve_floor": _money(self.emergency_reserve_floor),
            "emergency_reserve_target": _money(self.emergency_reserve_target),
            "near_term_committed_cash": self.near_term_committed_cash.canonical(),
            "protected_liquidity": _money(self.protected_liquidity),
            "spendable_surplus": _money(self.spendable_surplus),
            "critical_debt_balance": self.critical_debt_balance.canonical(),
            "critical_debt_ids": list(self.critical_debt_ids),
            "protection_gap": _money(self.protection_gap),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "planning_date": self.planning_date.isoformat(),
            "engine_version": self.engine_version,
            "profile_hash": self.profile_hash,
        }

    def to_dict(self) -> dict[str, object]:
        result = self.material_dict()
        result["state_hash"] = self.state_hash
        return result


def _emergency_fund_months(liquid_assets: Money, monthly_essential_expenses: Money) -> str | None:
    """Informational ratio only; the hard guardrail compares Money amounts directly (§17-19)."""
    if monthly_essential_expenses.is_zero():
        return None
    try:
        ratio = _ROUNDING_CONTEXT.divide(liquid_assets.amount, monthly_essential_expenses.amount)
        ratio = ratio.quantize(_RATIO_QUANTIZE, context=_ROUNDING_CONTEXT)
    except DecimalException as exc:
        # Reachable: Money permits amounts up to ~47 significant digits before the ratio's
        # digit count (bounded by _ROUNDING_CONTEXT's prec=50) is exceeded by extreme
        # liquid_assets / expenses combinations (see test_state.py's boundary coverage).
        raise InvalidValueError("emergency fund months ratio is not computable") from exc
    return f"{ratio:.{_RATIO_PLACES}f}"


def _near_term_committed_cash(
    profile: FinancialProfile, context: FinancialPlanningContext, horizon_months: int
) -> Money:
    horizon_end = _add_months(context.planning_date, horizon_months)
    return Money.sum(
        need.amount
        for need in profile.committed_cash_needs
        if need.mandatory and context.planning_date <= need.due_date <= horizon_end
    )


def _critical_debt(
    profile: FinancialProfile, activated_policy: ActivatedFinancialPolicy
) -> tuple[Money, tuple[str, ...]]:
    threshold = activated_policy.policy.critical_debt_apr
    critical = [debt for debt in profile.debts if debt.annual_percentage_rate >= threshold]
    balance = Money.sum(debt.outstanding_balance for debt in critical)
    ids = tuple(debt.debt_id for debt in critical)
    return balance, ids


def _liquidity_metrics(
    liquid_assets: Money,
    expenses: Money,
    policy_floor_months: int,
    policy_target_months: int,
    near_term_committed_cash: Money,
) -> tuple[Money, Money, str | None, Money, Money, tuple[FinancialReasonCode, ...]]:
    """Compute the expenses-known branch of financial-state figures (§17-21)."""
    floor = expenses.times(policy_floor_months)
    target = expenses.times(policy_target_months)
    reasons: list[FinancialReasonCode] = []
    months: str | None = None
    if expenses.is_zero():
        reasons.append(FinancialReasonCode.ZERO_ESSENTIAL_EXPENSE_BASE)
    else:
        months = _emergency_fund_months(liquid_assets, expenses)
    protected_liquidity = floor + near_term_committed_cash
    spendable_surplus = (liquid_assets - protected_liquidity).floor_at_zero()
    reasons.append(
        FinancialReasonCode.EMERGENCY_FUND_BELOW_FLOOR
        if liquid_assets < floor
        else FinancialReasonCode.EMERGENCY_FUND_PRESERVED
    )
    return floor, target, months, protected_liquidity, spendable_surplus, tuple(reasons)


def compute_financial_state(
    profile: FinancialProfile,
    activated_policy: ActivatedFinancialPolicy,
    context: FinancialPlanningContext,
    *,
    engine_version: str = FINANCIAL_STATE_ENGINE_VERSION,
) -> FinancialState:
    policy = activated_policy.policy
    temporal_findings = evaluate_financial_policy_temporal_readiness(policy, context.planning_date)
    if temporal_findings:
        raise FinancialValidationError(
            "financial policy is not effective for the planning date (fail closed): "
            + "; ".join(temporal_findings)
        )

    liquid_assets = profile.liquid_assets
    expenses = profile.monthly_essential_expenses
    liquid_assets_known = liquid_assets is not None
    expenses_known = expenses is not None

    if liquid_assets_known:
        assert liquid_assets is not None  # noqa: S101 - narrowed by liquid_assets_known above
        if context.available_budget > liquid_assets:
            raise FinancialValidationError(
                "available budget cannot exceed known liquid assets (fail closed)"
            )

    near_term_committed_cash = _near_term_committed_cash(
        profile, context, policy.near_term_liquidity_months
    )
    critical_debt_balance, critical_debt_ids = _critical_debt(profile, activated_policy)
    protection_gap = profile.protection.protection_gap

    emergency_reserve_floor: Money | None = None
    emergency_reserve_target: Money | None = None
    emergency_fund_months: str | None = None
    protected_liquidity: Money | None = None
    spendable_surplus: Money | None = None

    reasons: list[FinancialReasonCode] = []
    if not liquid_assets_known or not expenses_known:
        reasons.append(FinancialReasonCode.FINANCIAL_INPUT_REQUIRED)
    else:
        assert expenses is not None  # noqa: S101 - narrowed by expenses_known above
        assert liquid_assets is not None  # noqa: S101 - narrowed by liquid_assets_known above
        (
            emergency_reserve_floor,
            emergency_reserve_target,
            emergency_fund_months,
            protected_liquidity,
            spendable_surplus,
            liquidity_reasons,
        ) = _liquidity_metrics(
            liquid_assets,
            expenses,
            policy.emergency_floor_months,
            policy.emergency_target_months,
            near_term_committed_cash,
        )
        reasons.extend(liquidity_reasons)

    if near_term_committed_cash.is_positive():
        reasons.append(FinancialReasonCode.LIQUIDITY_COMMITMENT_CONFLICT)
    if critical_debt_balance.is_positive():
        reasons.append(FinancialReasonCode.CRITICAL_DEBT_PRESENT)
    if spendable_surplus is not None and spendable_surplus.is_zero():
        reasons.append(FinancialReasonCode.NO_SPENDABLE_SURPLUS)
    if protection_gap is not None and protection_gap.is_positive():
        reasons.append(FinancialReasonCode.PROTECTION_GAP)
    elif profile.protection.required_life_coverage is None:
        reasons.append(FinancialReasonCode.PROTECTION_NEED_UNKNOWN)

    status = (
        FinancialStateStatus.READY
        if (liquid_assets_known and expenses_known)
        else FinancialStateStatus.PARTIAL
    )
    state = FinancialState(
        status=status,
        liquid_assets=liquid_assets,
        monthly_essential_expenses=expenses,
        emergency_fund_months=emergency_fund_months,
        emergency_reserve_floor=emergency_reserve_floor,
        emergency_reserve_target=emergency_reserve_target,
        near_term_committed_cash=near_term_committed_cash,
        protected_liquidity=protected_liquidity,
        spendable_surplus=spendable_surplus,
        critical_debt_balance=critical_debt_balance,
        critical_debt_ids=critical_debt_ids,
        protection_gap=protection_gap,
        reason_codes=tuple(reasons),
        policy_id=policy.policy_id,
        policy_version=policy.version,
        policy_hash=activated_policy.content_hash,
        planning_date=context.planning_date,
        engine_version=engine_version,
        state_hash="",
        profile_hash=sha256_hex(canonical_json(profile.to_dict())),
    )
    return _with_hash(state)


def _with_hash(state: FinancialState) -> FinancialState:
    return replace(state, state_hash=sha256_hex(canonical_json(state.material_dict())))


class FinancialStateIntegrityError(InvalidValueError):
    """``FinancialState.state_hash`` does not match its own ``material_dict()`` (R1-02).

    Replay/snapshot trust boundaries must not trust a carried ``state_hash`` at face value;
    this recomputes it from the state's own material fields and fails closed on any mismatch,
    catching tampering that a changed ``GuardrailResult`` alone would not reveal (e.g. a
    financial-state mutation that happens to leave the final guardrail decision unchanged).
    """


def verify_financial_state_integrity(state: FinancialState) -> None:
    expected_hash = sha256_hex(canonical_json(state.material_dict()))
    if state.state_hash != expected_hash:
        raise FinancialStateIntegrityError(
            "financial state hash does not match its material fields (fail closed)"
        )
