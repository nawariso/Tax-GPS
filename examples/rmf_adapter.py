"""Strict private RMF transport parsing, with no tax eligibility decisions."""

from dataclasses import fields
from datetime import date
from typing import Any

from examples.demo_errors import input_scope, invalid_input
from tax_gps.calculation.pvd import pvd_parameter
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.rmf import RmfFacts, RmfReportConfirmation, RmfReportingStatus

RMF_LABELS = {
    "own_purchase_paid": "ยอดซื้อ RMF ด้วยเงินตนเองที่จ่ายจริงสะสมถึงวันที่ประเมิน",
    "fund_name": "ชื่อกองทุน RMF",
    "amc_name": "ชื่อบริษัทจัดการกองทุน (บลจ.)",
    "first_purchase_date": "วันที่ซื้อ RMF ครั้งแรก",
    "assessment_date": "วันที่ประเมินข้อมูล RMF",
    "reporting_status": "สถานะรายงานของ บลจ.",
    "report_confirmation": "หลักฐานยืนยันรายงานยอดปัจจุบัน",
    "ordinary_own_purchase_confirmed": "ตรวจเอกสารแล้วว่าเป็นการซื้อ RMF ปกติด้วยเงินตนเอง ไม่ใช่รับโอน",
    "single_fund": "ซื้อกองทุน RMF เดียว",
    "single_amc": "ซื้อผ่าน บลจ. เดียว",
    "first_ever_purchase_in_tax_year": "ซื้อ RMF ครั้งแรกในชีวิตในปีภาษีนี้",
    "paid_through_assessment_date": "ยอดที่กรอกเป็นยอดจ่ายจริงสะสมถึงวันที่ประเมิน ไม่รวมแผนซื้อในอนาคต",
    "declaration_completed": "แจ้งความประสงค์ใช้สิทธิกับ บลจ. แล้ว",
    "no_distributions_or_borrowing": "ปัจจุบันไม่มีการรับเงินปันผล รับเงินอื่น กู้ยืม หรือถอนจากกองทุน",
    "no_known_reporting_problem": "ไม่พบปัญหาหรือข้อมูลรายงานที่ต้องแก้ไข",
    "future_obligations_acknowledged": (
        "รับทราบหน้าที่ซื้อต่อเนื่อง ถือครองและไถ่ถอนตามเงื่อนไข รวมถึงไม่รับเงินหรือกู้ยืมจากกองทุน (ไม่ใช่ยืนยันว่าทำครบแล้ว)"
    ),
}


def render_rmf_terms(pack: ActivatedRulePack) -> str:
    """Show reviewed parameters before acknowledgement; no numeric adapter defaults."""
    rule = "RMF_CONTINUING_CONDITIONS"
    holding = pvd_parameter(pack, rule, "minimum_holding_years")
    age = pvd_parameter(pack, rule, "minimum_redemption_age")
    gap = pvd_parameter(pack, rule, "maximum_purchase_gap_years")
    return (
        f"เงื่อนไขถือครองอย่างน้อย {int(holding)} ปี และไถ่ถอนเมื่ออายุไม่น้อยกว่า "
        f"{int(age)} ปีตามเงื่อนไข ต้องซื้อต่อเนื่องโดยเว้นซื้อได้ไม่เกิน {int(gap)} ปีติดต่อกัน "
        "และต้องไม่รับเงินปันผลหรือเงินอื่น ไม่กู้ยืมหรือถอนเงินจากกองทุน "
        "ทั้งหมดเป็นหน้าที่ต่อเนื่องในอนาคต การรับทราบไม่ใช่การยืนยันว่าทำครบแล้ว"
    )


def _text(value: object, fact: str) -> str:
    if not isinstance(value, str):
        raise invalid_input(fact)
    return value


def _name(value: object, fact: str) -> str:
    text = _text(value, fact)
    if not text.strip() or len(text) > 100:
        raise invalid_input(fact)
    return text.strip()


def _confirmation(value: object) -> RmfReportConfirmation | None:
    if value is None:
        return None
    fact = "rmf.report_confirmation"
    keys = {"fund_name", "amc_name", "tax_year", "cumulative_paid", "confirmed_on"}
    if not isinstance(value, dict) or set(value) != keys:
        raise invalid_input(fact)
    with input_scope(fact):
        return RmfReportConfirmation(
            _name(value["fund_name"], fact),
            _name(value["amc_name"], fact),
            TaxYear(int(_text(value["tax_year"], fact))),
            Money.of(_text(value["cumulative_paid"], fact)),
            date.fromisoformat(_text(value["confirmed_on"], fact)),
        )


def parse_rmf_profile(value: object, *, assessment_date: date) -> RmfFacts | None:
    if value is None:
        return None
    names = {f.name for f in fields(RmfFacts)} - {"assessment_date"}
    if not isinstance(value, dict) or not set(value) <= names:
        raise invalid_input("rmf")
    parsed: dict[str, Any] = {"assessment_date": assessment_date}
    for key in sorted(names):
        fact = "rmf." + key
        if key == "report_confirmation":
            parsed[key] = _confirmation(value.get(key))
            continue
        raw = _text(value.get(key, ""), fact)
        with input_scope(fact):
            if raw == "":
                parsed[key] = None
            elif key == "own_purchase_paid":
                parsed[key] = Money.of(raw)
            elif key in ("fund_name", "amc_name"):
                parsed[key] = _name(raw, fact)
            elif key == "first_purchase_date":
                parsed[key] = date.fromisoformat(raw)
            elif key == "reporting_status":
                parsed[key] = RmfReportingStatus(raw)
            elif raw in ("true", "false"):
                parsed[key] = raw == "true"
            else:
                raise invalid_input(fact)
    with input_scope("rmf"):
        return RmfFacts(**parsed)


def rmf_reason(reason: str) -> str | None:
    if reason == "PVD_RMF_COMBINED_UNSUPPORTED":
        return "ยังไม่รองรับการมี PVD และซื้อ RMF ร่วมกัน · ข้อจำกัดของตัวทดลอง"
    if reason == "RMF_REPORTING_DISCREPANCY_UNSUPPORTED":
        return "รายงาน RMF มีปัญหาหรืออยู่ระหว่างแก้ไข จึงยังไม่เปิดประมาณการนี้"
    for key, label in RMF_LABELS.items():
        if reason == "RMF_" + key.upper() + "_UNSUPPORTED":
            return label + ": คำตอบไม่เข้าเส้นทางประมาณการนี้ · ข้อจำกัดของตัวทดลอง ไม่ใช่คำตัดสินว่าหมดสิทธิถาวร"
    return None
