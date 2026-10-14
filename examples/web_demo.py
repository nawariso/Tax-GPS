"""Loopback-only demonstration adapter; no persistence, recommendation or filing.

Run from the repository root: uv run python -m examples.web_demo
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tax_gps.candidate.activation import activate_allocation_policy, bundled_allocation_policy
from tax_gps.candidate.engine import build_candidates
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.engine import calculate_tax
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.policy import activate_financial_policy, bundled_financial_policy
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile
from tax_gps.financial.state import compute_financial_state
from tax_gps.opportunity.activation import activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, load_bundled_rule_pack
from tax_gps.profile.models import (
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    SharedLimitUsage,
    UserProfile,
)

ASSETS = Path(__file__).with_name("web")
FIELDS = frozenset(
    {"salary", "social_security", "assets", "expenses", "budget", "shared_usage", "planning_date"}
)
MAX_BODY = 4096
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def _money(data: dict[str, str], name: str) -> Money:
    value = data[name]
    if not re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", value):
        raise ValueError(f"{name}: enter a nonnegative THB amount with at most two decimals")
    return Money.of(value)


def calculate(data: object) -> dict[str, object]:
    """Compose the existing production activation path, never duplicate tax rules."""
    if (
        not isinstance(data, dict)
        or set(data) != FIELDS
        or not all(isinstance(value, str) for value in data.values())
    ):
        raise ValueError("Supply exactly the seven demo fields as strings")
    planning_date = date.fromisoformat(data["planning_date"])
    if planning_date.year != 2026:
        raise ValueError("This demo supports the bundled 2026 policy only")
    year = TaxYear(2026)
    usage = data["shared_usage"]
    profile = UserProfile(
        profile_id="local-demo",
        version="1",
        tax_year=year,
        income=IncomeProfile(section_40_1=_money(data, "salary")),
        benefits=ExistingTaxBenefits(social_security_paid=_money(data, "social_security")),
        opportunity_facts=OpportunityFacts(
            shared_limit_usage=(
                (SharedLimitUsage(THAI_ESG_2026_POOL, _money(data, "shared_usage")),)
                if usage != ""
                else None
            )
        ),
    )
    pack = activate_rule_pack(load_bundled_rule_pack(BUNDLED_PACK_ID_2026))
    catalog = activate_catalog(load_bundled_catalog())
    tax = calculate_tax(profile, pack)
    if tax.taxable_income is None or tax.pit is None:
        raise ValueError("Tax state is unsupported; no demonstration outcome is published")
    discovery = discover_opportunities(
        profile, tax, pack, catalog, DiscoveryContext(year, planning_date)
    )
    context = FinancialPlanningContext(planning_date, _money(data, "budget"))
    financial_policy = activate_financial_policy(bundled_financial_policy(year))
    financial = compute_financial_state(
        FinancialProfile(
            liquid_assets=_money(data, "assets") if data["assets"] != "" else None,
            monthly_essential_expenses=_money(data, "expenses"),
        ),
        financial_policy,
        context,
    )
    guards = evaluate_guardrails(discovery, financial, financial_policy, context)
    policy = activate_allocation_policy(
        bundled_allocation_policy(profile, tax, discovery, catalog),
        profile,
        tax,
        discovery,
        catalog,
    )
    outcomes = build_candidates(tax, discovery, financial, guards, policy)
    return {
        "taxable_income": tax.taxable_income.canonical(),
        "tax_before": tax.pit.canonical(),
        "financial": financial.to_dict(),
        "discovery": discovery.to_dict(),
        "guardrails": guards.to_dict(),
        "outcomes": outcomes.to_dict(),
        "demo_scope": "EMPLOYEE_40_1_ONLY_NO_DEBT_NO_COMMITMENTS_UNKNOWN_PROTECTION",
    }


class DemoHandler(BaseHTTPRequestHandler):
    """Serve an explicit asset allowlist; do not expose the repository."""

    def log_message(self, format: str, *args: object) -> None:
        """Do not log submitted personal data or request paths."""

    def _reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict[str, object]) -> None:
        self._reply(
            status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8"
        )

    def _local_request(self) -> bool:
        host = self.headers.get("Host", "")
        if not isinstance(self.server, ThreadingHTTPServer):
            return False
        port = self.server.server_port
        if host not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{host}"

    def do_GET(self) -> None:
        if not self._local_request():
            self._json(403, {"error": "Local browser requests only"})
        elif self.path in STATIC:
            name, content_type = STATIC[self.path]
            self._reply(200, (ASSETS / name).read_bytes(), content_type)
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self._local_request():
            self._json(403, {"error": "Local browser requests only"})
            return
        if self.path != "/api/calculate":
            self._json(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY or self.headers.get("Transfer-Encoding"):
                raise ValueError("Invalid request size")
            self.connection.settimeout(5)
            data = json.loads(self.rfile.read(size))
            result = calculate(data)
        except (ValueError, OSError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(200, result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), DemoHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
