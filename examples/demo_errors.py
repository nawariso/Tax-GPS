"""Public, structured demo errors; never include submitted financial amounts."""

from collections.abc import Iterator
from contextlib import contextmanager

FIELD_LABELS = {
    "salary": "เงินเดือน",
    "social_security": "เงินสมทบประกันสังคม",
    "assets": "สินทรัพย์สภาพคล่อง",
    "expenses": "ค่าใช้จ่ายจำเป็น",
    "budget": "งบทดลอง",
    "planning_date": "วันที่วางแผน",
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
    return f"{FIELD_LABELS[root]} ({field_id})"


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
