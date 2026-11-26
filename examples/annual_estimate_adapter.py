"""Private JSON transport for the local annual estimate."""

from datetime import date

from examples.demo_errors import FIELD_LABELS, input_scope, invalid_input
from examples.demo_profile import optional_amount, optional_boolean, parse_annual_rights
from examples.pvd_adapter import c02_reason
from tax_gps.calculation.annual_estimate import (
    AnnualEstimateInput,
    AnnualEstimateInputError,
    AnnualEstimateResult,
    EstimatePeriod,
    calculate_annual_estimate,
)
from tax_gps.calculation.annual_estimate_audit import (
    annual_estimate_outputs,
    annual_estimate_snapshot,
)
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import load_bundled_rule_pack
from tax_gps.profile.models import SharedLimitUsage
from tax_gps.profile.pvd import PvdWageBasisError
from tax_gps.profile.rmf import RmfFactConflictError

_FIELDS = {
    "cutoff_date",
    "confirmed_for",
    "actual",
    "forecast",
    "social_security",
    "shared_usage",
    "profile",
    "pvd_forecast_single_employer",
}
_PERIOD_FIELDS = {"wages", "bonus", "withholding", "outside_coverage"}
_BASELINE_MESSAGES = {
    "ACTUAL_OUTSIDE_COVERAGE": "ยังไม่รองรับรายได้นอกขอบเขตในช่วงยอดจริง",
    "FORECAST_OUTSIDE_COVERAGE": "ยังไม่รองรับรายได้นอกขอบเขตในช่วงที่เหลือ",
    "RETIREMENT_BASELINE_UNSUPPORTED": "ยังไม่รองรับเงินออมเกษียณในฐานภาษี",
    "PRIOR_SHARED_USAGE_BASELINE_UNSUPPORTED": "ยังไม่รองรับยอดลงทุนเดิมที่ใช้สิทธิไปแล้ว",
    "SHARED_USAGE_REQUIRED": "ยังไม่ทราบยอดใช้วงเงินเดิม Thai ESG / ESGX",
    "PARENT_ELIGIBILITY_REQUIRED": "ยังไม่ทราบสิทธิบิดามารดา",
}


def _text(value: object, fact_id: str) -> str:
    if not isinstance(value, str):
        raise invalid_input(fact_id)
    return value


def _date(value: object, fact_id: str) -> date | None:
    with input_scope(fact_id):
        raw = _text(value, fact_id)
        return date.fromisoformat(raw) if raw else None


def _period(value: object, name: str) -> EstimatePeriod:
    if not isinstance(value, dict) or set(value) != _PERIOD_FIELDS:
        raise invalid_input(name)
    wages, bonus, withholding = (
        optional_amount(_text(value[key], f"{name}.{key}"), f"{name}.{key}")
        for key in ("wages", "bonus", "withholding")
    )
    fact_id = f"{name}.outside_coverage"
    return EstimatePeriod(
        wages,
        bonus,
        withholding,
        optional_boolean(_text(value["outside_coverage"], fact_id), fact_id),
    )


def _baseline_error(result: AnnualEstimateResult) -> str:
    messages = [
        _BASELINE_MESSAGES[reason] if reason in _BASELINE_MESSAGES else c02_reason(reason)
        for reason in result.baseline.reason_codes
        if reason != "UNSUPPORTED_INCOME"
    ]
    missing_labels = [
        FIELD_LABELS[fact] for fact in result.baseline.missing_fact_ids if fact in FIELD_LABELS
    ]
    if missing_labels:
        messages.append("โปรดตรวจ " + ", ".join(missing_labels))
    return " · ".join(messages) or "โปรดตรวจข้อมูลที่ระบุ"


def calculate_estimate(data: object) -> dict[str, object]:
    if not isinstance(data, dict) or set(data) != _FIELDS:
        raise invalid_input("request")
    pack = activate_rule_pack(load_bundled_rule_pack())
    cutoff = _date(data["cutoff_date"], "cutoff_date")
    shared = optional_amount(_text(data["shared_usage"], "shared_usage"), "shared_usage")
    social = optional_amount(_text(data["social_security"], "social_security"), "social_security")
    employer_id = "pvd_forecast_single_employer"
    with input_scope("profile"):
        inputs = AnnualEstimateInput(
            tax_year=pack.pack.tax_year,
            cutoff_date=cutoff,
            confirmed_for=_date(data["confirmed_for"], "confirmed_for"),
            actual=_period(data["actual"], "actual"),
            forecast=_period(data["forecast"], "forecast"),
            rights=parse_annual_rights(data["profile"], social=social, cutoff=cutoff),
            shared_limit_usage=(SharedLimitUsage(THAI_ESG_2026_POOL, shared),)
            if shared is not None
            else None,
            pvd_forecast_single_employer=optional_boolean(
                _text(data[employer_id], employer_id), employer_id
            ),
        )
        try:
            result = calculate_annual_estimate(inputs, pack)
        except (AnnualEstimateInputError, RmfFactConflictError) as exc:
            raise invalid_input(exc.fact_id) from exc
        except PvdWageBasisError as exc:
            raise invalid_input("pvd.wage_basis") from exc
    response = annual_estimate_outputs(result)
    if result.tax is None:
        return response | {"export": None, "error": _baseline_error(result)}
    snapshot = annual_estimate_snapshot(inputs, result, pack)
    return response | {"export": snapshot.to_dict()}
