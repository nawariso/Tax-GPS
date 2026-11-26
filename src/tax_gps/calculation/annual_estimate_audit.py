"""Versioned annual estimate export and deterministic replay."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import cast

from tax_gps.audit import AuditReplayError
from tax_gps.calculation.annual_estimate import (
    AnnualEstimateInput,
    AnnualEstimateResult,
    AnnualEstimateRights,
    EstimatePeriod,
    calculate_annual_estimate,
)
from tax_gps.core.canonical import JsonValue, canonical_json, freeze, sha256_hex, thaw
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import ENGINE_VERSION
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import (
    Child,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    RetirementContribution,
    SharedLimitUsage,
    UserProfile,
)
from tax_gps.profile.pvd import FundHistoryFacts, OtherRightsFacts, PvdFacts
from tax_gps.profile.rmf import RmfFacts, RmfReportConfirmation, RmfReportingStatus

SCHEMA = "tax-gps-annual-estimate/1"


@dataclass(frozen=True, slots=True)
class AnnualEstimateSnapshot:
    result: AnnualEstimateResult
    _payload: JsonValue

    def to_dict(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], thaw(self._payload))


def _money_text(value: Money | None) -> str | None:
    return value.canonical() if value is not None else None


def _period_material(period: EstimatePeriod) -> dict[str, JsonValue]:
    return {
        "wages": _money_text(period.wages),
        "bonus": _money_text(period.bonus),
        "withholding": _money_text(period.withholding),
        "outside_coverage": period.outside_coverage,
    }


def _pack_material(pack: ActivatedRulePack) -> dict[str, JsonValue]:
    return {
        "rule_pack_id": pack.rule_pack_id,
        "version": pack.version,
        "content_hash": pack.content_hash,
    }


def annual_estimate_outputs(result: AnnualEstimateResult) -> dict[str, object]:
    """Render the same result fields in HTTP and the audit payload."""
    return {
        "baseline_status": result.baseline.status.value,
        "reason_codes": list(result.baseline.reason_codes),
        "missing_fact_ids": list(result.baseline.missing_fact_ids),
        "tax": result.tax.to_dict() if result.tax is not None else None,
        "settlement_status": result.settlement_status.value,
        "withholding_missing_fact_ids": list(result.withholding_missing_fact_ids),
        "annual_withholding": _money_text(result.annual_withholding),
        "settlement_kind": result.settlement_kind.value
        if result.settlement_kind is not None
        else None,
        "settlement_amount": _money_text(result.settlement_amount),
    }


def annual_estimate_snapshot(
    inputs: AnnualEstimateInput, result: AnnualEstimateResult, pack: ActivatedRulePack
) -> AnnualEstimateSnapshot:
    """Capture a ready result from the same calculation request."""
    if result.tax is None:
        raise AuditReplayError("annual baseline is not ready")
    profile = UserProfile(
        profile_id="annual-estimate",
        version="1",
        tax_year=inputs.tax_year,
        income=IncomeProfile(cast(Money, result.tax.income.gross_income)),
        benefits=inputs.rights.confirmed_benefits(),
        opportunity_facts=OpportunityFacts(shared_limit_usage=inputs.shared_limit_usage),
    ).to_dict()
    material = {
        "tax_year": inputs.tax_year.gregorian,
        "cutoff_date": cast(date, inputs.cutoff_date).isoformat(),
        "confirmed_for": cast(date, inputs.confirmed_for).isoformat(),
        "actual": _period_material(inputs.actual),
        "forecast": _period_material(inputs.forecast),
        "rights": profile["benefits"],
        "shared_limit_usage": cast(dict[str, object], profile["opportunity_facts"])[
            "shared_limit_usage"
        ],
        "pvd_forecast_single_employer": inputs.pvd_forecast_single_employer,
    }
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "engine_version": ENGINE_VERSION,
        "pack": _pack_material(pack),
        "material": material,
        "outputs": annual_estimate_outputs(result),
    }
    payload["snapshot_hash"] = sha256_hex(canonical_json(payload))
    return AnnualEstimateSnapshot(result, freeze(payload))


def create_annual_estimate_snapshot(
    inputs: AnnualEstimateInput, pack: ActivatedRulePack
) -> AnnualEstimateSnapshot:
    return annual_estimate_snapshot(inputs, calculate_annual_estimate(inputs, pack), pack)


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise TypeError("expected snapshot record")
    return value


def _sequence(value: JsonValue) -> tuple[JsonValue, ...]:
    if not isinstance(value, list | tuple):
        raise TypeError("expected snapshot array")
    return tuple(value)


def _money(value: JsonValue) -> Money | None:
    return None if value is None else Money.of(cast(str, value))


def _date(value: JsonValue) -> date | None:
    return None if value is None else date.fromisoformat(cast(str, value))


def _tax_year(value: JsonValue) -> TaxYear:
    return TaxYear(cast(int, value))


def _boolean(value: JsonValue) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise TypeError("expected snapshot boolean")
    return value


def _record[T](
    value: JsonValue, model: Callable[..., T], **decoders: Callable[[JsonValue], object]
) -> T:
    raw = _mapping(value)
    fields: dict[str, object] = dict(raw)
    for field, decode in decoders.items():
        fields[field] = decode(raw[field])
    return model(**fields)


def _confirmation(value: JsonValue) -> RmfReportConfirmation | None:
    if value is None:
        return None
    return _record(
        value,
        RmfReportConfirmation,
        tax_year=_tax_year,
        cumulative_paid=_money,
        confirmed_on=_date,
    )


def _reporting(value: JsonValue) -> RmfReportingStatus | None:
    return None if value is None else RmfReportingStatus(cast(str, value))


def _rmf(value: JsonValue) -> RmfFacts | None:
    if value is None:
        return None
    return _record(
        value,
        RmfFacts,
        own_purchase_paid=_money,
        first_purchase_date=_date,
        assessment_date=_date,
        reporting_status=_reporting,
        report_confirmation=_confirmation,
    )


def _rights(value: JsonValue) -> AnnualEstimateRights:
    rights = _mapping(value)
    return AnnualEstimateRights(
        parents=tuple(_record(row, Parent) for row in _sequence(rights["parents"])),
        children=tuple(_record(row, Child) for row in _sequence(rights["children"])),
        retirement_contributions=tuple(
            _record(row, RetirementContribution, amount_used=_money)
            for row in _sequence(rights["retirement_contributions"])
        ),
        pvd=_record(rights["pvd"], PvdFacts, employee_paid=_money, wage_basis=_money),
        other_rights=_record(rights["other_rights"], OtherRightsFacts),
        fund_history=_record(rights["fund_history"], FundHistoryFacts),
        rmf=_rmf(rights["rmf"]),
        personal_eligible=_boolean(rights["personal_eligible"]),
        social_security_paid=_money(rights["social_security_paid"]),
        mortgage_interest_paid=_money(rights["mortgage_interest_paid"]),
        mortgage_eligible=_boolean(rights["mortgage_eligible"]),
    )


def _period(value: JsonValue) -> EstimatePeriod:
    return _record(
        value,
        EstimatePeriod,
        wages=_money,
        bonus=_money,
        withholding=_money,
        outside_coverage=_boolean,
    )


def _inputs(value: JsonValue) -> AnnualEstimateInput:
    data = _mapping(value)
    return AnnualEstimateInput(
        tax_year=_tax_year(data["tax_year"]),
        cutoff_date=_date(data["cutoff_date"]),
        confirmed_for=_date(data["confirmed_for"]),
        actual=_period(data["actual"]),
        forecast=_period(data["forecast"]),
        rights=_rights(data["rights"]),
        shared_limit_usage=tuple(
            _record(row, SharedLimitUsage, amount_used=_money)
            for row in _sequence(data["shared_limit_usage"])
        ),
        pvd_forecast_single_employer=_boolean(data["pvd_forecast_single_employer"]),
    )


def replay_annual_estimate(
    snapshot: Mapping[str, JsonValue], pack: ActivatedRulePack
) -> AnnualEstimateResult:
    if (snapshot.get("schema"), snapshot.get("engine_version"), snapshot.get("pack")) != (
        SCHEMA,
        ENGINE_VERSION,
        _pack_material(pack),
    ):
        raise AuditReplayError("annual estimate version or rule pack does not match")
    try:
        rebuilt = create_annual_estimate_snapshot(_inputs(snapshot["material"]), pack)
        expected, supplied = canonical_json(rebuilt.to_dict()), canonical_json(snapshot)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise AuditReplayError("invalid annual estimate snapshot") from exc
    if expected != supplied:
        raise AuditReplayError("annual estimate snapshot does not match replay")
    return rebuilt.result
