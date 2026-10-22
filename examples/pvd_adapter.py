"""Strict C02A input mapping and Thai labels; no tax calculations."""

from dataclasses import fields
from typing import Any

from examples.demo_errors import input_scope, invalid_input
from tax_gps.core.money import Money
from tax_gps.profile.pvd import FundHistoryFacts, OtherRightsFacts, PvdFacts

PVD_LABELS = {
    "employee_paid": "เงินสะสมของคุณที่เข้ากองทุนจริงในปีนี้",
    "wage_basis": "ฐานค่าจ้างในช่วงที่จ่ายเงินสะสม PVD",
    "fund_name": "ชื่อหรือรหัสกองทุน PVD",
    "registered_fund": "กองทุนจดทะเบียน",
    "credited_in_tax_year": "เงินสะสมเข้ากองทุนจริงในปีภาษีนี้",
    "single_employer": "นายจ้างเดียวตลอดปี ไม่มีเปลี่ยนงาน",
    "single_fund": "เงินสะสมจากกองทุนเดียว",
    "ordinary_article_rate": "อัตราปกติตามข้อบังคับกองทุน ไม่มีข้อยกเว้นพิเศษ",
    "normal_remittance": "นำส่งตามกำหนดปกติ ไม่มีล่าช้า พักหรือเลื่อนนำส่ง",
}
OTHER_LABELS = {
    "rmf": "RMF",
    "thai_esg": "Thai ESG",
    "thai_esgx": "Thai ESGX",
    "gpf": "กบข.",
    "teacher_fund": "กองทุนสงเคราะห์ครูเอกชน",
    "nsf": "กอช.",
    "pension_insurance": "ประกันบำนาญ",
    "ssf": "SSF",
    "spouse_pvd_claim": "สิทธิ PVD จากคู่สมรส",
    "other_retirement_right": "สิทธิเกษียณอื่น",
}
HISTORY_LABELS = {
    "prior_conditional_rights": (
        "ประวัติใช้สิทธิ RMF / SSF / ESG / LTF ที่ยังมีเงื่อนไขต่อเนื่อง (นอกเหนือ PVD ปกติ)"
    ),
    "disposal_withdrawal_transfer": "ประวัติขาย ถอน หรือโอนกองทุนในปีนี้",
    "retirement_or_recapture": "ประวัติเกษียณหรือคืนสิทธิภาษีในปีนี้",
    "ltf_carryforward": "สิทธิสืบเนื่องจาก LTF",
}


def _group[T: (PvdFacts, OtherRightsFacts, FundHistoryFacts)](
    value: object, name: str, model: type[T]
) -> T | None:
    if value is None:
        return None
    names = {item.name for item in fields(model)}
    if not isinstance(value, dict) or not set(value) <= names:
        raise invalid_input(name)
    result: dict[str, Any] = {}
    for key in names:
        raw = value.get(key, "")
        field_id = f"{name}.{key}"
        if not isinstance(raw, str):
            raise invalid_input(field_id)
        with input_scope(field_id):
            if raw == "":
                result[key] = None
            elif key in ("employee_paid", "wage_basis"):
                amount = Money.of(raw)
                if amount.is_negative():
                    raise invalid_input(field_id)
                result[key] = amount
            elif key == "fund_name":
                if not raw.strip() or len(raw) > 100:
                    raise invalid_input(field_id)
                result[key] = raw.strip()
            elif raw in ("true", "false"):
                result[key] = raw == "true"
            else:
                raise invalid_input(field_id)
    return model(**result)


def parse_pvd_profile(
    value: object,
) -> tuple[PvdFacts | None, OtherRightsFacts | None, FundHistoryFacts | None]:
    if not isinstance(value, dict):
        raise invalid_input("profile")
    return (
        _group(value.get("pvd"), "pvd", PvdFacts),
        _group(value.get("other_rights"), "other_rights", OtherRightsFacts),
        _group(value.get("fund_history"), "fund_history", FundHistoryFacts),
    )


def c02_reason(reason: str) -> str:
    if reason == "C02A_FACTS_REQUIRED":
        return "ยังไม่ทราบข้อมูล PVD สิทธิอื่น หรือประวัติกองทุน โปรดตรวจรายการที่ต้องกรอก"
    if reason == "PVD_RATE_OUTSIDE_NORMAL_SCOPE":
        return "อัตราเงินสะสม PVD อยู่นอกกรณีปกติที่รองรับ"
    failure_labels = {
        "registered_fund": "กองทุนที่ยังไม่ได้จดทะเบียนตามกฎหมาย PVD",
        "credited_in_tax_year": "เงินสะสมที่ยังไม่ได้เข้ากองทุนจริงในปีภาษีนี้",
        "single_employer": "มีหลายนายจ้างหรือเปลี่ยนงานในปีเดียวกัน",
        "single_fund": "เงินสะสมจากหลายกองทุน",
        "ordinary_article_rate": "อัตราพิเศษหรือไม่ใช่อัตราปกติตามข้อบังคับกองทุน",
        "normal_remittance": "นำส่งล่าช้า พัก เลื่อน หรือผิดปกติ",
    }
    for name, label in failure_labels.items():
        if reason == f"PVD_{name.upper()}_UNSUPPORTED":
            return f"ยังไม่รองรับกรณี: {label} · เป็นข้อจำกัดของตัวทดลองนี้"
    for prefix, labels in [
        ("OTHER_RIGHTS", OTHER_LABELS),
        ("FUND_HISTORY", HISTORY_LABELS),
    ]:
        for name, label in labels.items():
            if reason == f"{prefix}_{name.upper()}_UNSUPPORTED":
                return f"ยังไม่รองรับกรณี: {label}"
    return "ข้อมูลอยู่นอกขอบเขตที่รองรับ"
