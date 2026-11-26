"""Versioned C04A Thai ESG what-if export and deterministic replay."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import cast

from tax_gps.audit import AuditReplayError
from tax_gps.calculation.annual_estimate import AnnualEstimateInput
from tax_gps.calculation.annual_estimate_audit import (
    annual_estimate_snapshot,
    decode_annual_estimate_input,
)
from tax_gps.candidate.thai_esg_what_if import (
    WHAT_IF_ENGINE_VERSION,
    ThaiEsgWhatIfInput,
    ThaiEsgWhatIfResult,
    WhatIfStatus,
    evaluate_thai_esg_what_if,
)
from tax_gps.core.canonical import JsonValue, canonical_json, freeze, sha256_hex, thaw
from tax_gps.core.money import Money
from tax_gps.financial.policy import ActivatedFinancialPolicy
from tax_gps.financial.profile import (
    CommittedCashNeed,
    Debt,
    DebtCategory,
    FinancialProfile,
    ProtectionProfile,
)
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.policy.activation import ActivatedRulePack

SCHEMA = "tax-gps-thai-esg-what-if/1"


@dataclass(frozen=True, slots=True)
class ThaiEsgWhatIfSnapshot:
    result: ThaiEsgWhatIfResult
    _payload: JsonValue

    def to_dict(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], thaw(self._payload))


def _money_text(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


def thai_esg_what_if_outputs(result: ThaiEsgWhatIfResult) -> dict[str, object]:
    """Render the same what-if fields in HTTP and the audit payload."""
    impact = result.impact
    return {
        "status": result.status.value,
        "reason_codes": list(result.reason_codes),
        "missing_fact_ids": list(result.missing_fact_ids),
        "amount": _money_text(result.amount),
        "capacity": result.capacity.to_dict() if result.capacity is not None else None,
        "capacity_basis": result.capacity_basis.value
        if result.capacity_basis is not None
        else None,
        "guardrail": result.guardrail.to_dict() if result.guardrail is not None else None,
        "impact": {
            "taxable_before": impact.taxable_before.canonical(),
            "taxable_after": impact.taxable_after.canonical(),
            "pit_before": impact.pit_before.canonical(),
            "pit_after": impact.pit_after.canonical(),
            "saving": impact.saving.canonical(),
        }
        if impact is not None
        else None,
        "settlement_after_kind": result.settlement_after_kind.value
        if result.settlement_after_kind is not None
        else None,
        "settlement_after_amount": _money_text(result.settlement_after_amount),
        "lockup": result.lockup.to_dict() if result.lockup is not None else None,
        "evidence_requirements": [item.to_dict() for item in result.evidence_requirements],
    }


def _versions(
    catalog: ActivatedOpportunityCatalog, financial_policy: ActivatedFinancialPolicy
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "engine_version": WHAT_IF_ENGINE_VERSION,
        "catalog": {
            "catalog_id": catalog.catalog_id,
            "version": catalog.version,
            "content_hash": catalog.content_hash,
        },
        "financial_policy": {
            "policy_id": financial_policy.policy_id,
            "version": financial_policy.version,
            "content_hash": financial_policy.content_hash,
        },
    }


def create_thai_esg_what_if_snapshot(  # noqa: PLR0917 - mirrors the evaluation inputs
    estimate_input: AnnualEstimateInput,
    amount: Money,
    financial: FinancialProfile,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    financial_policy: ActivatedFinancialPolicy,
) -> ThaiEsgWhatIfSnapshot:
    """Evaluate and capture a READY what-if; other statuses have no export."""
    result = evaluate_thai_esg_what_if(
        estimate_input, ThaiEsgWhatIfInput(amount, financial), pack, catalog, financial_policy
    )
    if result.status is not WhatIfStatus.READY:
        raise AuditReplayError("Thai ESG what-if is not ready")
    payload: dict[str, object] = {
        **_versions(catalog, financial_policy),
        "annual_estimate": annual_estimate_snapshot(
            estimate_input, result.estimate, pack
        ).to_dict(),
        "material": {"amount": amount.canonical(), "financial": financial.to_dict()},
        "outputs": thai_esg_what_if_outputs(result),
    }
    payload["snapshot_hash"] = sha256_hex(canonical_json(payload))
    return ThaiEsgWhatIfSnapshot(result, freeze(payload))


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise TypeError("expected snapshot record")
    return value


def _rows(value: JsonValue) -> tuple[Mapping[str, JsonValue], ...]:
    if not isinstance(value, list | tuple):
        raise TypeError("expected snapshot array")
    return tuple(_mapping(row) for row in value)


def _money(value: JsonValue) -> Money | None:
    return None if value is None else Money.of(cast(str, value))


def _financial(value: JsonValue) -> FinancialProfile:
    data = _mapping(value)
    protection = _mapping(data["protection"])
    return FinancialProfile(
        liquid_assets=_money(data["liquid_assets"]),
        monthly_essential_expenses=_money(data["monthly_essential_expenses"]),
        debts=tuple(
            Debt(
                cast(str, row["debt_id"]),
                DebtCategory(cast(str, row["category"])),
                Money.of(cast(str, row["outstanding_balance"])),
                Decimal(cast(str, row["annual_percentage_rate"])),
                Money.of(cast(str, row["minimum_monthly_payment"])),
                cast(bool, row["secured"]),
            )
            for row in _rows(data["debts"])
        ),
        committed_cash_needs=tuple(
            CommittedCashNeed(
                cast(str, row["need_id"]),
                Money.of(cast(str, row["amount"])),
                date.fromisoformat(cast(str, row["due_date"])),
                cast(bool, row["mandatory"]),
                cast(str, row["description"]),
            )
            for row in _rows(data["committed_cash_needs"])
        ),
        protection=ProtectionProfile(
            _money(protection["required_life_coverage"]),
            _money(protection["existing_life_coverage"]),
        ),
    )


def replay_thai_esg_what_if(
    snapshot: Mapping[str, JsonValue],
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    financial_policy: ActivatedFinancialPolicy,
) -> ThaiEsgWhatIfResult:
    versions = _versions(catalog, financial_policy)
    if any(snapshot.get(key) != expected for key, expected in versions.items()):
        raise AuditReplayError("Thai ESG what-if version, catalog or policy does not match")
    try:
        material = _mapping(snapshot["material"])
        estimate = _mapping(snapshot["annual_estimate"])
        rebuilt = create_thai_esg_what_if_snapshot(
            decode_annual_estimate_input(estimate["material"]),
            Money.of(cast(str, material["amount"])),
            _financial(material["financial"]),
            pack,
            catalog,
            financial_policy,
        )
        expected, supplied = canonical_json(rebuilt.to_dict()), canonical_json(snapshot)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise AuditReplayError("invalid Thai ESG what-if snapshot") from exc
    if expected != supplied:
        raise AuditReplayError("Thai ESG what-if snapshot does not match replay")
    return rebuilt.result
