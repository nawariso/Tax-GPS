"""Public, structured demo errors; never include submitted financial amounts."""

from collections.abc import Iterator
from contextlib import contextmanager

FIELD_LABELS = {
    "salary": "เงินเดือน",
    "rmf": "ข้อมูล RMF",
    "pvd": "ข้อมูลเงินสะสม PVD",
    "other_rights": "สิทธิอื่นในปีนี้",
    "fund_history": "ประวัติกองทุน",
    "social_security": "เงินสมทบประกันสังคม",
    "assets": "สินทรัพย์สภาพคล่อง",
    "expenses": "ค่าใช้จ่ายจำเป็น",
    "budget": "งบทดลอง",
    "planning_date": "วันที่วางแผน",
    "cutoff_date": "วันตัดข้อมูล",
    "confirmed_for": "การยืนยันข้อมูลตามวันตัด",
    "pvd_forecast_single_employer": "นายจ้างเดียวในช่วงที่เหลือ",
    "tax_year": "ปีภาษี",
    "actual.wages": "ค่าจ้างที่ได้รับจริง",
    "actual.bonus": "โบนัสที่ได้รับจริง",
    "actual.withholding": "ภาษีหัก ณ ที่จ่ายจริง",
    "actual.outside_coverage": "รายได้นอกขอบเขตในช่วงจริง",
    "forecast.wages": "ค่าจ้างที่คาดในช่วงที่เหลือ",
    "forecast.bonus": "โบนัสที่คาดในช่วงที่เหลือ",
    "forecast.withholding": "ภาษีหัก ณ ที่จ่ายที่คาดในช่วงที่เหลือ",
    "forecast.outside_coverage": "รายได้นอกขอบเขตในช่วงที่เหลือ",
    "actual": "ยอดจริง",
    "forecast": "ยอดคาดช่วงที่เหลือ",
    "thai_esg_what_if": "การทดลองซื้อ Thai ESG",
    "thai_esg_what_if.amount": "จำนวนเงินที่จะลองซื้อ Thai ESG",
    "financial.liquid_assets": "สินทรัพย์สภาพคล่อง",
    "financial.monthly_essential_expenses": "ค่าใช้จ่ายจำเป็นต่อเดือน",
    "shared_usage": "ยอดใช้สิทธิเดิม Thai ESG / ESGX",
    "personal_eligible": "สิทธิส่วนตัว",
    "mortgage_interest": "ดอกเบี้ยบ้าน",
    "mortgage_eligible": "สิทธิดอกเบี้ยบ้าน",
    "other_income": "รายได้อื่น",
    "retirement_usage": "เงินออมเกษียณ",
    "required_coverage": "ความคุ้มครองที่ต้องการ",
    "existing_coverage": "ความคุ้มครองที่มี",
    "parent": "บิดามารดา",
    "parents": "บิดามารดา",
    "children": "บุตร",
    "debts": "หนี้",
    "commitments": "ภาระจ่าย",
    "profile": "ข้อมูลเพิ่มเติม",
    "request": "คำขอคำนวณ",
}


def field_label(field_id: str) -> str:
    root = field_id.split("[", 1)[0].split(".", 1)[0]
    return (
        f"{FIELD_LABELS[field_id] if field_id in FIELD_LABELS else FIELD_LABELS[root]} ({field_id})"
    )


class DemoInputError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "INPUT_REQUIRED",
        status: str = "REQUIRES_INPUT",
        reason_codes: tuple[str, ...] = (),
        missing_fact_ids: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.reason_codes = reason_codes
        self.missing_fact_ids = missing_fact_ids

    def to_dict(self) -> dict[str, object]:
        return {
            "error": str(self),
            "code": self.code,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "missing_fact_ids": list(self.missing_fact_ids),
        }


def invalid_input(field_id: str) -> DemoInputError:
    """Only code-owned paths are accepted here; submitted values are never formatted."""
    return DemoInputError(
        f"โปรดตรวจ{field_label(field_id)}: รูปแบบหรือขอบเขตไม่ถูกต้อง",
        code="INVALID_INPUT",
        reason_codes=("INVALID_INPUT",),
        missing_fact_ids=(field_id,),
    )


@contextmanager
def input_scope(field_id: str) -> Iterator[None]:
    """Preserve precise parser errors; safely locate constructor validation failures."""
    try:
        yield
    except DemoInputError:
        raise
    except ValueError as exc:
        raise invalid_input(field_id) from exc
