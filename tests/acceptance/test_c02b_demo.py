"""C02B AC01–08: explicit facts, reporting integrity and private adapter errors."""

import json
from dataclasses import fields
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from typing import Any, cast

import pytest
from examples.demo_errors import DemoInputError
from examples.web_demo import MAX_BODY, DemoHandler, calculate

from tax_gps.profile.rmf import RmfFacts
from tests.acceptance.test_c02a_demo import request


def rmf_request() -> dict[str, Any]:
    d = request("0")
    d["planning_date"] = "2026-10-22"
    d["profile"]["other_rights"]["rmf"] = "true"
    d["profile"]["rmf"] = {
        f.name: "true"
        for f in fields(RmfFacts)
        if f.name not in ("assessment_date", "report_confirmation")
    }
    d["profile"]["rmf"].update(
        own_purchase_paid="27000",
        fund_name="กองทุนทดสอบ",
        amc_name="บริษัททดสอบ",
        first_purchase_date="2026-01-02",
        reporting_status="NOT_YET_DUE",
        report_confirmation=None,
    )
    return d


def test_c02b_http_unknown_zero_positive_and_privacy() -> None:
    d = rmf_request()
    result = cast(dict[str, Any], calculate(d | {"assets": "", "expenses": "", "budget": ""}))
    assert result["planning_availability"] == "RMF_BASELINE_ONLY"
    assert result["taxable_income"] == "3000.00"
    assert result["financial"] is None
    assert result["outcomes"] is None
    assert result["rmf_conditions"]["assessment_date"] == "2026-10-22"
    assert result["estimate_label"] == "ประมาณการภายใต้เงื่อนไข RMF ที่ต้องปฏิบัติต่อเนื่อง"
    d["profile"]["rmf"]["own_purchase_paid"] = "98765-secret"
    with pytest.raises(DemoInputError) as e:
        calculate(d)
    assert "98765-secret" not in str(e.value)
    assert e.value.missing_fact_ids == ("rmf.own_purchase_paid",)


def test_c02b_http_stale_reporting_snapshot() -> None:
    d = rmf_request()
    f = d["profile"]["rmf"]
    f["reporting_status"] = "CONFIRMED_SUBMITTED"
    f["report_confirmation"] = {
        "fund_name": f["fund_name"],
        "amc_name": f["amc_name"],
        "tax_year": "2026",
        "cumulative_paid": "27000",
        "confirmed_on": "2026-10-01",
    }
    assert (
        cast(dict[str, Any], calculate(d))["rmf_conditions"]["report_confirmation"][
            "cumulative_paid"
        ]
        == "27000.00"
    )
    f["own_purchase_paid"] = "28000"
    with pytest.raises(DemoInputError) as e:
        calculate(d)
    assert e.value.missing_fact_ids == ("rmf.report_confirmation",)


def test_c02b_http_full_thai_request_size() -> None:
    """AC08: real bounded HTTP with confirmation and representative Thai records."""
    d = rmf_request()
    p = d["profile"]
    f = p["rmf"]
    f["reporting_status"] = "CONFIRMED_SUBMITTED"
    f["report_confirmation"] = {
        "fund_name": f["fund_name"],
        "amc_name": f["amc_name"],
        "tax_year": "2026",
        "cumulative_paid": "27000",
        "confirmed_on": "2026-10-01",
    }
    p["parents"] = [{"relationship": "father", "eligible": "true"}]
    p["children"] = [
        {"child_id": "บุตรคนแรก", "order": "1", "birth_year": "2015", "legally_eligible": "true"}
    ]
    p["debts"] = [
        {
            "debt_id": "สินเชื่อบ้านตัวอย่าง",
            "category": "MORTGAGE",
            "balance": "1000000",
            "apr_percent": "4.5",
            "minimum_payment": "8000",
            "secured": "true",
        }
    ]
    p["commitments"] = [
        {
            "need_id": "ค่าใช้จ่ายการศึกษา",
            "amount": "10000",
            "due_date": "2026-11-01",
            "mandatory": "true",
            "description": "ค่าใช้จ่ายการศึกษาประจำภาคเรียนของบุตร",
        }
    ]
    body = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(body) <= MAX_BODY
    with ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            conn.request("POST", "/api/calculate", body, {"Content-Type": "application/json"})
            response = conn.getresponse()
            result = json.loads(response.read())
            assert response.status == 200, result
            assert result["planning_availability"] == "RMF_BASELINE_ONLY"
            conn.close()
            conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            conn.request(
                "POST",
                "/api/calculate",
                b" " * (MAX_BODY + 1),
                {"Content-Type": "application/json"},
            )
            response = conn.getresponse()
            response.read()
            assert response.status == 400
        finally:
            conn.close()
            server.shutdown()
            thread.join(timeout=5)
