"""Local demonstration: real engine outcomes, validation and HTTP boundaries."""

import importlib.util
import json
from collections.abc import Iterator
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import ModuleType

import pytest

DEFAULTS = {
    "salary": "990500",
    "social_security": "10500",
    "assets": "500000",
    "expenses": "50000",
    "budget": "100000",
    "shared_usage": "0",
    "planning_date": "2026-10-14",
}


def _demo() -> ModuleType:
    path = Path(__file__).parents[2] / "examples" / "web_demo.py"
    assert path.is_file(), "Working web demonstration is not implemented yet"
    spec = importlib.util.spec_from_file_location("tax_gps_local_demo", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_real_engine_outcomes_and_determinism() -> None:
    demo = _demo()
    result = demo.calculate(DEFAULTS)
    assert result == demo.calculate(DEFAULTS)
    before, after = result["outcomes"]["candidates"]
    assert before["tax_after"] == "79000.00"
    assert after["tax_after"] == "60500.00"
    assert after["tax_saved"] == "18500.00"
    assert after["cash_outflow"] == "100000.00"
    assert after["spendable_surplus_after"] == "250000.00"


@pytest.mark.parametrize(
    ("changes", "allocation", "surplus"),
    [
        ({"assets": "200000"}, "50000.00", "0.00"),
        ({"budget": "0"}, "0.00", "350000.00"),
        ({"assets": "", "budget": "0"}, "0.00", None),
        ({"shared_usage": ""}, "0.00", "350000.00"),
        ({"shared_usage": "290000"}, "7150.00", "342850.00"),
        ({"salary": "200000"}, "60000.00", "290000.00"),
    ],
)
def test_demo_preserves_caps_zero_and_unknown(
    changes: dict[str, str], allocation: str, surplus: str | None
) -> None:
    result = _demo().calculate(DEFAULTS | changes)
    candidate = result["outcomes"]["candidates"][-1]
    assert candidate["cash_outflow"] == allocation
    assert candidate["spendable_surplus_after"] == surplus


@pytest.mark.parametrize(
    "changes",
    [
        {"salary": "-1"},
        {"salary": "NaN"},
        {"salary": "0.001"},
        {"salary": 990500},
        {"assets": "1"},
        {"planning_date": "2027-01-01"},
        {"planning_date": "not-a-date"},
        {"shared_usage": "-1"},
        {"unexpected": "field"},
    ],
)
def test_demo_rejects_invalid_inputs(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r".+"):
        _demo().calculate(DEFAULTS | changes)


def test_demo_http_and_private_files() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _demo().DemoHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 200
        assert "Tax GPS" in response.read().decode()
        for path in ("/app.js", "/style.css"):
            connection.request("GET", path)
            response = connection.getresponse()
            assert response.status == 200
            assert response.read()
        for path in ("/.env", "/../README.md", "/src/tax_gps/engine.py"):
            connection.request("GET", path)
            response = connection.getresponse()
            assert response.status == 404
            response.read()
        connection.request(
            "POST", "/api/calculate", json.dumps(DEFAULTS), {"Content-Type": "application/json"}
        )
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read())["outcomes"]["candidates"][1]["tax_saved"] == "18500.00"
        connection.request("POST", "/api/calculate", "{}", {"Origin": "https://untrusted.example"})
        response = connection.getresponse()
        assert response.status == 403
        response.read()
        connection.request("POST", "/api/calculate", "invalid")
        response = connection.getresponse()
        assert response.status == 400
        response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def demo_server() -> Iterator[ThreadingHTTPServer]:
    with ThreadingHTTPServer(("127.0.0.1", 0), _demo().DemoHandler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


@pytest.mark.parametrize(
    ("method", "path", "body", "headers", "status"),
    [
        ("GET", "/", None, {"Host": "untrusted.example"}, 403),
        ("GET", "/", None, {"Origin": "null"}, 403),
        ("POST", "/unknown", None, {}, 404),
        ("POST", "/api/calculate", "", {}, 400),
        ("POST", "/api/calculate", None, {"Content-Length": "4097"}, 400),
        ("POST", "/api/calculate", None, {"Content-Length": "bad"}, 400),
        # Reject ambiguous transfer framing before waiting for any request body.
        (
            "POST",
            "/api/calculate",
            None,
            {"Content-Length": "2", "Transfer-Encoding": "chunked"},
            400,
        ),
        ("POST", "/api/calculate", "[]", {}, 400),
    ],
)
def test_demo_http_boundaries(
    demo_server: ThreadingHTTPServer,
    *,
    method: str,
    path: str,
    body: str | None,
    headers: dict[str, str],
    status: int,
) -> None:
    connection = HTTPConnection("127.0.0.1", demo_server.server_port, timeout=5)
    try:
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        assert response.status == status
        assert response.getheader("Cache-Control") == "no-store"
        assert response.getheader("X-Content-Type-Options") == "nosniff"
        assert "frame-ancestors 'none'" in str(response.getheader("Content-Security-Policy"))
        assert json.loads(response.read())["error"]
    finally:
        connection.close()
