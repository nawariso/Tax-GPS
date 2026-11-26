"""Private JSON transport for the local annual estimate."""

from datetime import date

from examples.demo_errors import FIELD_LABELS, DemoInputError, input_scope, invalid_input
from examples.demo_profile import (
    optional_amount,
    optional_boolean,
    parse_annual_rights,
    parse_thai_esg_what_if,
)
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
from tax_gps.candidate.thai_esg_what_if import (
    ThaiEsgWhatIfInput,
    ThaiEsgWhatIfInputError,
    ThaiEsgWhatIfResult,
    WhatIfStatus,
    evaluate_thai_esg_what_if,
)
from tax_gps.candidate.thai_esg_what_if_audit import (
    create_thai_esg_what_if_snapshot,
    thai_esg_what_if_outputs,
)
from tax_gps.core.money import Money
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tax_gps.financial.profile import FinancialProfile
from tax_gps.opportunity.activation import activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.policy.activation import ActivatedRulePack, activate_rule_pack
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
_WHAT_IF_FIELD = "thai_esg_what_if"
_GUARDRAIL_MESSAGES = {
    "EMERGENCY_FUND_BELOW_FLOOR": "เงินสำรองฉุกเฉินต่ำกว่าขั้นต่ำ ระบบจึงไม่เปิดใช้เงินเพิ่ม",
    "CRITICAL_DEBT_PRESENT": "มีหนี้ดอกเบี้ยสูง ระบบจึงไม่เปิดใช้เงินเพิ่มเพื่อสิทธิภาษี",
    "ALLOCATION_CAPPED_BY_LIQUIDITY": "จำนวนนี้เกินสภาพคล่องที่ใช้ได้หลังกันเงินสำรอง",
    "NO_SPENDABLE_SURPLUS": "ไม่มีสภาพคล่องเหลือหลังกันเงินสำรอง",
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


def _what_if_error(result: ThaiEsgWhatIfResult) -> str | None:
    status = result.status
    if status is WhatIfStatus.READY:
        return None
    if status is WhatIfStatus.BASELINE_NOT_READY:
        return "ยังทดลองซื้อ Thai ESG ไม่ได้ เพราะประมาณการภาษีทั้งปียังไม่พร้อม"
    if status is WhatIfStatus.UNSUPPORTED:
        return "ยังไม่เปิดทดลองซื้อ Thai ESG สำหรับกรณีที่ซื้อ RMF ในปีนี้"
    if status is WhatIfStatus.REQUIRES_INPUT:
        return "โปรดระบุ " + ", ".join(FIELD_LABELS[fact] for fact in result.missing_fact_ids)
    if status is WhatIfStatus.EXCEEDS_TAX_CAPACITY:
        return "จำนวนนี้เกินวงเงินสิทธิ Thai ESG ที่เหลือ จึงไม่คำนวณภาษีของจำนวนนี้"
    reasons = [
        _GUARDRAIL_MESSAGES[code] for code in result.reason_codes if code in _GUARDRAIL_MESSAGES
    ]
    return " · ".join(reasons) or "จำนวนนี้เกินยอดที่การตรวจเงินสำรองอนุญาต"


def _invalid_what_if(error: DemoInputError) -> dict[str, object]:
    """A bad what-if field closes only the what-if; the message never echoes the value."""
    return {
        "status": "INVALID_INPUT",
        "reason_codes": list(error.reason_codes),
        "missing_fact_ids": list(error.missing_fact_ids),
        "amount": None,
        "capacity": None,
        "capacity_basis": None,
        "guardrail": None,
        "impact": None,
        "settlement_after_kind": None,
        "settlement_after_amount": None,
        "lockup": None,
        "evidence_requirements": [],
        "export": None,
        "error": str(error),
    }


def _what_if_response(
    inputs: AnnualEstimateInput, raw: object, pack: ActivatedRulePack
) -> dict[str, object]:
    try:
        chosen, financial = parse_thai_esg_what_if(raw)
        return _what_if(inputs, chosen, financial, pack)
    except DemoInputError as exc:
        return _invalid_what_if(exc)


def _what_if(
    inputs: AnnualEstimateInput,
    chosen: Money | None,
    financial: FinancialProfile,
    pack: ActivatedRulePack,
) -> dict[str, object]:
    catalog = activate_catalog(load_bundled_catalog())
    policy = activate_financial_policy(bundled_financial_policy(pack.pack.tax_year))
    with input_scope(_WHAT_IF_FIELD):
        try:
            result = evaluate_thai_esg_what_if(
                inputs, ThaiEsgWhatIfInput(chosen, financial), pack, catalog, policy
            )
        except ThaiEsgWhatIfInputError as exc:
            raise invalid_input(exc.fact_id) from exc
    exported = (
        create_thai_esg_what_if_snapshot(
            inputs, result.amount, financial, pack, catalog, policy
        ).to_dict()
        if result.status is WhatIfStatus.READY and result.amount is not None
        else None
    )
    return thai_esg_what_if_outputs(result) | {"export": exported, "error": _what_if_error(result)}


def calculate_estimate(data: object) -> dict[str, object]:
    if not isinstance(data, dict) or set(data) - {_WHAT_IF_FIELD} != _FIELDS:
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
    if _WHAT_IF_FIELD in data:
        response[_WHAT_IF_FIELD] = _what_if_response(inputs, data[_WHAT_IF_FIELD], pack)
    if result.tax is None:
        return response | {"export": None, "error": _baseline_error(result)}
    snapshot = annual_estimate_snapshot(inputs, result, pack)
    return response | {"export": snapshot.to_dict()}
