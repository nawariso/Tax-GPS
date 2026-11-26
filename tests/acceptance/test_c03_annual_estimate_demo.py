"""C03-AC01–09: the HTTP route is a private adapter for the domain result."""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from typing import Any

import pytest
from examples.annual_estimate_adapter import calculate_estimate
from examples.demo_errors import DemoInputError
from examples.web_demo import MAX_BODY, calculate

from tests.acceptance import test_web_demo
from tests.support.demo_profiles import explicit_demo_profile

annual_demo_server = test_web_demo.demo_server


def request_data() -> dict[str, Any]:
    profile = explicit_demo_profile()
    for field in ("debts", "commitments", "required_coverage", "existing_coverage", "other_income"):
        profile.pop(field)
    return {
        "cutoff_date": "2026-10-31",
        "confirmed_for": "2026-10-31",
        "actual": {
            "wages": "600000",
            "bonus": "40000",
            "withholding": "45000",
            "outside_coverage": "false",
        },
        "forecast": {
            "wages": "300500",
            "bonus": "50000",
            "withholding": "30000",
            "outside_coverage": "false",
        },
        "social_security": "0",
        "shared_usage": "0",
        "profile": profile,
        "pvd_forecast_single_employer": "",
    }


def test_c03_http_partial_ready_and_raw_inputs_stay_private() -> None:
    request = request_data()
    request["forecast"]["withholding"] = ""
    response: dict[str, Any] = calculate_estimate(request)
    assert response["baseline_status"] == "READY"
    assert response["tax"]["pit"] == "81100.00"
    assert response["settlement_status"] == "REQUIRES_INPUT"
    assert response["withholding_missing_fact_ids"] == ["forecast.withholding"]
    assert response["settlement_amount"] is None
    assert response["export"]["outputs"]["settlement_amount"] is None
    assert response["export"]["material"]["forecast"]["withholding"] is None
    assert "outcomes" not in response
    request["actual"]["wages"] = ""
    request["forecast"]["outside_coverage"] = "true"
    request["profile"]["children"] = [
        {
            "child_id": "test-child",
            "order": "1",
            "birth_year": "2019",
            "legally_eligible": "unknown",
        }
    ]
    blocked: dict[str, Any] = calculate_estimate(request)
    assert blocked["baseline_status"] == "ADVANCED_TAX_PATH_REQUIRED"
    assert "FORECAST_OUTSIDE_COVERAGE" in blocked["reason_codes"]
    assert "ช่วงที่เหลือ" in blocked["error"]
    assert "children[0].legally_eligible" in blocked["missing_fact_ids"]
    assert blocked["tax"] is blocked["settlement_amount"] is blocked["export"] is None
    request["actual"]["wages"] = "-541234.67"
    with pytest.raises(DemoInputError) as error:
        calculate_estimate(request)
    assert error.value.missing_fact_ids == ("actual.wages",)
    assert "541234" not in str(error.value)


def test_c03_http_year_end_validation_and_existing_route() -> None:
    request = request_data()
    request["cutoff_date"] = request["confirmed_for"] = "2026-12-31"
    request["actual"].update(wages="900500", bonus="90000", withholding="75000")
    request["forecast"].update(wages="0", bonus="0", withholding="0")
    result: dict[str, Any] = calculate_estimate(request)
    assert result["settlement_amount"] == "6100.00"
    request["forecast"]["withholding"] = ""
    assert calculate_estimate(request)["settlement_status"] == "REQUIRES_INPUT"
    request["forecast"]["withholding"] = "0.01"
    with pytest.raises(DemoInputError) as error:
        calculate_estimate(request)
    assert error.value.missing_fact_ids == ("forecast.withholding",)
    legacy: dict[str, Any] = calculate(test_web_demo.DEFAULTS)
    assert legacy["tax_before"] == "79000.00"
    assert legacy["outcomes"]["candidates"]
    assert "settlement_status" not in legacy


def test_c03_http_real_route_and_body_limits(annual_demo_server: ThreadingHTTPServer) -> None:
    def post(
        path: str, body: str, headers: dict[str, str] | None = None
    ) -> tuple[int, dict[str, Any]]:
        with_connection = HTTPConnection("127.0.0.1", annual_demo_server.server_port, timeout=5)
        try:
            with_connection.request("POST", path, body, headers or {})
            response = with_connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            with_connection.close()

    path = "/api/annual-estimate"
    body = json.dumps(request_data())
    status, data = post(path, body)
    assert status == 200
    assert data["settlement_amount"] == "6100.00"
    assert data["export"]["schema"] == "tax-gps-annual-estimate/1"
    assert post(path, body, {"Host": "example.invalid"})[0] == 403
    assert post(path, body, {"Origin": "https://example.invalid"})[0] == 403
    assert post(path, " " * (MAX_BODY + 1))[0] == 400
    assert post("/api/calculate", json.dumps(test_web_demo.DEFAULTS))[0] == 200
