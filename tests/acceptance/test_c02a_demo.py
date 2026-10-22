"""C02A-AC01/05/07: HTTP adapter preserves authoritative readiness."""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from typing import Any, cast

import pytest
from examples.demo_errors import DemoInputError
from examples.web_demo import MAX_BODY, DemoHandler, calculate

from tests.acceptance.test_demo_profile import DEFAULTS, _profile


def request(paid: str = "27000") -> dict[str, Any]:
    profile = _profile()
    profile["pvd"] = {
        "employee_paid": paid,
        "wage_basis": "180000",
        "fund_name": "Test fund",
        **dict.fromkeys(
            (
                "registered_fund",
                "credited_in_tax_year",
                "single_employer",
                "single_fund",
                "ordinary_article_rate",
                "normal_remittance",
            ),
            "true",
        ),
    }
    profile["other_rights"] = dict.fromkeys(
        (
            "rmf",
            "thai_esg",
            "thai_esgx",
            "gpf",
            "teacher_fund",
            "nsf",
            "pension_insurance",
            "ssf",
            "spouse_pvd_claim",
            "other_retirement_right",
        ),
        "false",
    )
    profile["fund_history"] = dict.fromkeys(
        (
            "prior_conditional_rights",
            "disposal_withdrawal_transfer",
            "retirement_or_recapture",
            "ltf_carryforward",
        ),
        "false",
    )
    return DEFAULTS | {"salary": "180000", "social_security": "0", "profile": profile}


def test_c02a_http_missing_zero_positive_and_history() -> None:
    data = request()
    result = cast(dict[str, Any], calculate(data | {"assets": "", "expenses": "", "budget": ""}))
    assert result["taxable_income"] == "11500.00"
    assert result["planning_availability"] == "PVD_BASELINE_ONLY"
    assert result["outcomes"] is None
    assert result["financial"] is None
    assert result["guardrails"] is None
    assert result["pvd"]["exemption"] == "17000.00"
    del data["profile"]["pvd"]
    with pytest.raises(DemoInputError) as error:
        calculate(data)
    assert error.value.code == "BASELINE_NOT_READY"
    assert "pvd.employee_paid" in error.value.missing_fact_ids
    data = request("0")
    data["profile"]["fund_history"]["prior_conditional_rights"] = "true"
    with pytest.raises(DemoInputError) as error:
        calculate(data)
    assert error.value.status == "UNSUPPORTED"
    assert "ประวัติ" in str(error.value)


def test_c02a_http_privacy_and_bounds() -> None:
    data = request()
    data["profile"]["pvd"]["employee_paid"] = "987654321-secret"
    with pytest.raises(DemoInputError) as error:
        calculate(data)
    assert "987654321-secret" not in str(error.value)
    assert "pvd.employee_paid" in error.value.missing_fact_ids
    data = request()
    data["profile"]["pvd"]["employer_paid"] = "5000"
    with pytest.raises(DemoInputError):
        calculate(data)


@pytest.mark.parametrize("wage", ["0", "180001"])
def test_c02a_contradictory_wage_keeps_field_metadata(wage: str) -> None:
    """C02A-AC07 / final review Important1."""
    data = request()
    data["profile"]["pvd"]["wage_basis"] = wage
    with pytest.raises(DemoInputError) as error:
        calculate(data)
    assert error.value.missing_fact_ids == ("pvd.wage_basis",)
    assert error.value.code == "INVALID_INPUT"
    assert "180001" not in str(error.value)


@pytest.mark.parametrize(
    ("field", "explanation"),
    [
        ("registered_fund", "ยังไม่ได้จดทะเบียน"),
        ("credited_in_tax_year", "ยังไม่ได้เข้ากองทุนจริง"),
        ("single_employer", "หลายนายจ้างหรือเปลี่ยนงาน"),
        ("single_fund", "หลายกองทุน"),
        ("ordinary_article_rate", "อัตราพิเศษหรือไม่ใช่อัตราปกติ"),
        ("normal_remittance", "นำส่งล่าช้า พัก เลื่อน หรือผิดปกติ"),
    ],
)
def test_c02a_false_facts_name_the_excluded_case(field: str, explanation: str) -> None:
    """C02A-AC02/05/07 / final review Important2."""
    data = request()
    data["profile"]["pvd"][field] = "false"
    with pytest.raises(DemoInputError) as error:
        calculate(data)
    assert error.value.status == "UNSUPPORTED"
    assert explanation in str(error.value)
    assert "ข้อจำกัดของตัวทดลอง" in str(error.value)


@pytest.mark.parametrize("paid", ["0", "27000"])
def test_c02a_complete_thai_profile_fits_http_body_limit(paid: str) -> None:
    """C02A-AC07: representative UTF-8 records reach both real HTTP paths."""
    data = request(paid)
    profile = data["profile"]
    profile["pvd"]["fund_name"] = "กองทุนสำรองเลี้ยงชีพพนักงานบริษัทตัวอย่างซึ่งจดทะเบียนแล้ว"
    profile["parents"] = [{"relationship": "father", "eligible": "true"}]
    profile["children"] = [
        {"child_id": "บุตรคนแรก", "order": "1", "birth_year": "2015", "legally_eligible": "true"}
    ]
    profile["debts"] = [
        {
            "debt_id": "สินเชื่อบ้านตัวอย่าง",
            "category": "MORTGAGE",
            "balance": "1000000",
            "apr_percent": "4.5",
            "minimum_payment": "8000",
            "secured": "true",
        }
    ]
    profile["commitments"] = [
        {
            "need_id": "ค่าใช้จ่ายการศึกษา",
            "amount": "10000",
            "due_date": "2026-11-01",
            "mandatory": "true",
            "description": "ค่าใช้จ่ายการศึกษาประจำภาคเรียนของบุตร",
        }
    ]
    profile["required_coverage"] = "1000000"
    profile["existing_coverage"] = "500000"
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(body) <= MAX_BODY
    with ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request("POST", "/api/calculate", body, {"Content-Type": "application/json"})
            response = connection.getresponse()
            result = json.loads(response.read())
            assert response.status == 200, result
            expected = "AVAILABLE" if paid == "0" else "PVD_BASELINE_ONLY"
            assert result["planning_availability"] == expected
        finally:
            connection.close()
            server.shutdown()
            thread.join(timeout=5)
