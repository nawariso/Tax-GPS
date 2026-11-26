"""Extended demo profile maps explicit facts to the unchanged core."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from examples.demo_errors import DemoInputError

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.financial.profile import ProtectionProfile
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, load_bundled_rule_pack
from tax_gps.profile.models import (
    Child,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    UserProfile,
)
from tests.support.demo_profiles import explicit_demo_profile
from tests.support.profiles import complete_benefits

DEFAULTS = {
    "profile": explicit_demo_profile(),
    "salary": "990500",
    "social_security": "10500",
    "assets": "500000",
    "expenses": "50000",
    "budget": "100000",
    "shared_usage": "0",
    "planning_date": "2026-10-14",
}


def _demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "tax_gps_extended_demo", Path(__file__).parents[2] / "examples" / "web_demo.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _profile() -> dict[str, object]:
    return explicit_demo_profile() | {
        "personal_eligible": "true",
        "parents": [],
        "children": [],
        "mortgage_interest": "0",
        "mortgage_eligible": "false",
        "debts": [],
        "commitments": [],
        "required_coverage": "",
        "existing_coverage": "",
        "other_income": "0",
        "retirement_usage": "0",
    }


def test_family_uses_existing_core_tax_path() -> None:
    profile = _profile() | {
        "parents": [{"relationship": "father", "eligible": "true"}],
        "children": [
            {"child_id": "child-1", "order": "1", "birth_year": "2015", "legally_eligible": "true"},
            {"child_id": "child-2", "order": "2", "birth_year": "2020", "legally_eligible": "true"},
        ],
        "mortgage_interest": "140000",
        "mortgage_eligible": "true",
    }
    result = _demo().calculate(DEFAULTS | {"profile": profile})
    expected = calculate_tax(
        UserProfile(
            opportunity_facts=OpportunityFacts(shared_limit_usage=()),
            profile_id="local-demo",
            version="1",
            tax_year=TaxYear(2026),
            income=IncomeProfile(Money.of("990500")),
            benefits=complete_benefits(
                social_security_paid=Money.of("10500"),
                parents=(Parent("father", True),),
                children=(
                    Child("child-1", True, 2015, order=1),
                    Child("child-2", True, 2020, order=2),
                ),
                mortgage_interest_paid=Money.of("140000"),
                mortgage_eligible=True,
            ),
        ),
        activate_rule_pack(load_bundled_rule_pack(BUNDLED_PACK_ID_2026)),
    )
    assert expected.pit is not None
    assert result["tax_before"] == expected.pit.canonical()
    assert result["tax_state"]["allowances"] == expected.to_dict()["allowances"]
    assert result == _demo().calculate(DEFAULTS | {"profile": profile})


def test_critical_debt_blocks_new_tax_cash() -> None:
    profile = _profile() | {
        "debts": [
            {
                "debt_id": "card-1",
                "category": "CREDIT_CARD",
                "balance": "120000",
                "apr_percent": "24.125",
                "minimum_payment": "5000",
                "secured": "false",
            }
        ]
    }
    result = _demo().calculate(DEFAULTS | {"profile": profile})
    assert result["financial"]["critical_debt_balance"] == "120000.00"
    assert all(
        candidate["cash_outflow"] == "0.00" for candidate in result["outcomes"]["candidates"]
    )
    assert (
        result["submitted_profile"]["financial"]["debts"][0]["annual_percentage_rate"] == "0.24125"
    )


def test_commitments_cap_cash_and_preserve_unknown_cover() -> None:
    profile = _profile() | {
        "commitments": [
            {
                "need_id": "tuition",
                "amount": "300000",
                "due_date": "2026-11-01",
                "mandatory": "true",
                "description": "ค่าเรียน",
            }
        ]
    }
    result = _demo().calculate(DEFAULTS | {"profile": profile})
    assert result["financial"]["near_term_committed_cash"] == "300000.00"
    assert result["outcomes"]["candidates"][-1]["cash_outflow"] == "50000.00"
    assert result["financial"]["protection_gap"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"personal_eligible": "unknown"},
        {"mortgage_eligible": "unknown"},
        {"other_income": "100"},
        {"other_income": ""},
        {"retirement_usage": "100"},
        {"retirement_usage": ""},
        {"parents": [{"relationship": "father", "eligible": "unknown"}]},
        {
            "children": [
                {"child_id": "c", "order": "1", "birth_year": "2020", "legally_eligible": "unknown"}
            ]
        },
        {"debts": [{}]},
        {"commitments": [{}]},
        {"unknown_field": "0"},
        {"required_coverage": "-1"},
        {"parents": "[]"},
    ],
)
def test_profile_fails_closed(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r".+"):
        _demo().calculate(DEFAULTS | {"profile": _profile() | changes})


def test_protection_and_unknown_expenses() -> None:
    profile = _profile() | {"required_coverage": "1000000", "existing_coverage": "200000"}
    result = _demo().calculate(DEFAULTS | {"profile": profile, "expenses": ""})
    expected = ProtectionProfile(Money.of("1000000"), Money.of("200000")).protection_gap
    assert expected is not None
    assert result["financial"]["protection_gap"] == expected.canonical()
    assert result["financial"]["status"] == "PARTIAL"
    assert all(
        candidate["cash_outflow"] == "0.00" for candidate in result["outcomes"]["candidates"]
    )


@pytest.mark.parametrize(
    ("top", "changes", "code", "status", "reasons", "missing"),
    [
        (
            {"shared_usage": "100000"},
            {},
            "BASELINE_NOT_READY",
            "UNSUPPORTED",
            ("PRIOR_SHARED_USAGE_BASELINE_UNSUPPORTED",),
            (),
        ),
        (
            {"shared_usage": ""},
            {},
            "BASELINE_NOT_READY",
            "REQUIRES_INPUT",
            ("SHARED_USAGE_REQUIRED",),
            ("opportunity_facts.shared_limit_usage",),
        ),
        (
            {},
            {"retirement_usage": "100000"},
            "BASELINE_NOT_READY",
            "UNSUPPORTED",
            ("RETIREMENT_BASELINE_UNSUPPORTED",),
            (),
        ),
        (
            {},
            {"retirement_usage": ""},
            "INPUT_REQUIRED",
            "REQUIRES_INPUT",
            ("RETIREMENT_INPUT_REQUIRED",),
            ("retirement_usage",),
        ),
        (
            {},
            {"other_income": ""},
            "INPUT_REQUIRED",
            "REQUIRES_INPUT",
            ("OTHER_INCOME_INPUT_REQUIRED",),
            ("other_income",),
        ),
        (
            {},
            {"other_income": "100000"},
            "BASELINE_NOT_READY",
            "ADVANCED_TAX_PATH_REQUIRED",
            ("UNSUPPORTED_INCOME",),
            (),
        ),
        (
            {},
            {"parents": [{"relationship": "father", "eligible": "unknown"}]},
            "INPUT_REQUIRED",
            "REQUIRES_INPUT",
            ("PARENT_ELIGIBILITY_REQUIRED",),
            ("parent.father.eligible",),
        ),
    ],
)
def test_c01_extended_profile_errors_are_structured_without_amounts(
    *,
    top: dict[str, str],
    changes: dict[str, object],
    code: str,
    status: str,
    reasons: tuple[str, ...],
    missing: tuple[str, ...],
) -> None:
    """C01-AC09/AC11: extended profiles close the baseline with machine reasons."""
    with pytest.raises(DemoInputError) as caught:
        _demo().calculate(DEFAULTS | top | {"profile": _profile() | changes})
    error = caught.value
    assert getattr(error, "code", None) == code
    assert getattr(error, "status", None) == status
    assert getattr(error, "reason_codes", None) == reasons
    assert getattr(error, "missing_fact_ids", None) == missing
    assert "100000" not in str(error)
