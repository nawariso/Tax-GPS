"""C04A-AC01–10: the annual-estimate HTTP route carries an optional Thai ESG what-if."""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from typing import Any

import pytest
from examples.annual_estimate_adapter import calculate_estimate

from tax_gps.candidate.thai_esg_what_if import WhatIfStatus
from tax_gps.candidate.thai_esg_what_if_audit import replay_thai_esg_what_if
from tax_gps.core.tax_year import TaxYear
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tests.acceptance import test_web_demo
from tests.acceptance.test_c02b_demo import rmf_request
from tests.acceptance.test_c03_annual_estimate_demo import request_data
from tests.support.catalog import production_catalog
from tests.support.policy import production_pack

what_if_demo_server = test_web_demo.demo_server


def what_if(**changes: Any) -> dict[str, Any]:
    block: dict[str, Any] = {
        "amount": "100000",
        "assets": "1000000",
        "expenses": "30000",
        "debts": [],
        "commitments": [],
        "required_coverage": "",
        "existing_coverage": "",
    }
    block.update(changes)
    return block


def with_what_if(**changes: Any) -> dict[str, Any]:
    request = request_data()
    request["thai_esg_what_if"] = what_if(**changes)
    return request


def test_c04a_http_without_block_keeps_c03_response() -> None:
    """C04A-AC10: the existing C03 contract is unchanged when no what-if is sent."""
    response: dict[str, Any] = calculate_estimate(request_data())
    assert "thai_esg_what_if" not in response
    assert response["settlement_amount"] == "6100.00"


def test_c04a_http_ready_what_if_matches_reference_and_replays() -> None:
    """C04A-AC01/10: ESG-100K over HTTP; the export replays."""
    response: dict[str, Any] = calculate_estimate(with_what_if())
    assert response["tax"]["pit"] == "81100.00"
    block = response["thai_esg_what_if"]
    assert block["status"] == "READY"
    assert block["error"] is None
    assert block["impact"]["pit_after"] == "62075.00"
    assert block["impact"]["saving"] == "19025.00"
    assert block["settlement_after_kind"] == "REFUND"
    assert block["settlement_after_amount"] == "12925.00"
    assert block["capacity"]["remaining_capacity"] == "297150.00"
    exported = block["export"]
    assert exported["schema"] == "tax-gps-thai-esg-what-if/1"
    assert exported["annual_estimate"] == response["export"]
    result = replay_thai_esg_what_if(
        exported,
        production_pack(),
        production_catalog(),
        activate_financial_policy(bundled_financial_policy(TaxYear(2026))),
    )
    assert result.status is WhatIfStatus.READY


@pytest.mark.parametrize(
    ("changes", "status", "message"),
    [
        ({"amount": ""}, "REQUIRES_INPUT", "จำนวนเงินที่จะลองซื้อ Thai ESG"),
        ({"assets": "", "expenses": ""}, "REQUIRES_INPUT", "สินทรัพย์สภาพคล่อง"),
        ({"amount": "297150.01"}, "EXCEEDS_TAX_CAPACITY", "เกินวงเงินสิทธิ Thai ESG"),
        ({"assets": "50000"}, "GUARDRAIL_LIMITED", "เงินสำรองฉุกเฉิน"),
        (
            {
                "debts": [
                    {
                        "debt_id": "card",
                        "category": "CREDIT_CARD",
                        "balance": "20000",
                        "apr_percent": "18",
                        "minimum_payment": "2000",
                        "secured": "false",
                    }
                ]
            },
            "GUARDRAIL_LIMITED",
            "หนี้ดอกเบี้ยสูง",
        ),
        ({"assets": "190000", "amount": "100000.01"}, "GUARDRAIL_LIMITED", "สภาพคล่อง"),
    ],
)
def test_c04a_http_not_ready_what_if_keeps_c03_and_explains(
    changes: dict[str, Any], status: str, message: str
) -> None:
    """C04A-AC03/08 / D4: limits and unknowns close only the what-if, with Thai reasons."""
    response: dict[str, Any] = calculate_estimate(with_what_if(**changes))
    assert response["tax"]["pit"] == "81100.00"
    assert response["export"] is not None
    block = response["thai_esg_what_if"]
    assert block["status"] == status
    assert block["impact"] is None
    assert block["export"] is None
    assert message in block["error"]


def test_c04a_http_blocked_c03_closes_what_if() -> None:
    """C04A-AC06: C03 not READY publishes no what-if figures."""
    request = with_what_if()
    request["forecast"]["outside_coverage"] = "true"
    response: dict[str, Any] = calculate_estimate(request)
    assert response["tax"] is None
    block = response["thai_esg_what_if"]
    assert block["status"] == "BASELINE_NOT_READY"
    assert block["capacity"] is block["impact"] is block["export"] is None
    assert "ประมาณการภาษีทั้งปียังไม่พร้อม" in block["error"]


def test_c04a_http_rmf_positive_is_explained() -> None:
    """C04A-AC09: RMF purchase this year keeps the what-if closed in v0.1."""
    request = with_what_if()
    rmf = rmf_request()["profile"]
    request["profile"]["other_rights"] = rmf["other_rights"]
    request["profile"]["rmf"] = rmf["rmf"]
    response: dict[str, Any] = calculate_estimate(request)
    assert response["tax"] is not None
    block = response["thai_esg_what_if"]
    assert block["status"] == "UNSUPPORTED"
    assert block["reason_codes"] == ["RMF_BASELINE_ONLY"]
    assert "RMF" in block["error"]
    assert block["impact"] is block["export"] is None


@pytest.mark.parametrize(
    ("changes", "fact"),
    [
        ({"amount": "-1"}, "thai_esg_what_if.amount"),
        ({"amount": "1.001"}, "thai_esg_what_if.amount"),
        ({"assets": "abc"}, "assets"),
        ({"debts": [{"debt_id": "x"}]}, "debts[0]"),
    ],
)
def test_c04a_http_invalid_what_if_input_keeps_c03(changes: dict[str, Any], fact: str) -> None:
    """C04A-AC08: a bad what-if field closes only the what-if; C03 stays visible."""
    response: dict[str, Any] = calculate_estimate(with_what_if(**changes))
    assert response["tax"]["pit"] == "81100.00"
    assert response["export"] is not None
    block = response["thai_esg_what_if"]
    assert block["status"] == "INVALID_INPUT"
    assert block["missing_fact_ids"] == [fact]
    assert block["impact"] is block["capacity"] is block["export"] is None
    assert block["evidence_requirements"] == []
    for value in ("-1", "1.001", "abc"):
        if value in changes.values():
            assert value not in block["error"]


def test_c04a_http_unknown_block_shape_closes_only_what_if() -> None:
    request = request_data()
    request["thai_esg_what_if"] = {"amount": "1"}
    response: dict[str, Any] = calculate_estimate(request)
    assert response["tax"]["pit"] == "81100.00"
    assert response["thai_esg_what_if"]["status"] == "INVALID_INPUT"
    assert response["thai_esg_what_if"]["missing_fact_ids"] == ["thai_esg_what_if"]


def test_c04a_http_year_end_what_if() -> None:
    """C04A-AC01 at the 31 Dec cutoff over HTTP."""
    request = with_what_if()
    request["cutoff_date"] = request["confirmed_for"] = "2026-12-31"
    request["actual"].update(wages="900500", bonus="90000", withholding="75000")
    request["forecast"].update(wages="0", bonus="0", withholding="0")
    response: dict[str, Any] = calculate_estimate(request)
    block = response["thai_esg_what_if"]
    assert block["status"] == "READY"
    assert block["impact"]["pit_after"] == "62075.00"
    assert block["settlement_after_amount"] == "12925.00"


def test_c04a_http_real_route(what_if_demo_server: ThreadingHTTPServer) -> None:
    connection = HTTPConnection("127.0.0.1", what_if_demo_server.server_port, timeout=5)
    try:
        connection.request("POST", "/api/annual-estimate", json.dumps(with_what_if()))
        response = connection.getresponse()
        data = json.loads(response.read())
    finally:
        connection.close()
    assert response.status == 200
    assert data["thai_esg_what_if"]["export"]["schema"] == "tax-gps-thai-esg-what-if/1"
