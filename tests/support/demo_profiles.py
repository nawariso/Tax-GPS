"""Explicit no-rights/no-history synthetic HTTP scenario."""


def explicit_demo_profile() -> dict[str, object]:
    return {
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
        "pvd": {"employee_paid": "0"},
        "other_rights": dict.fromkeys(
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
        ),
        "fund_history": dict.fromkeys(
            (
                "prior_conditional_rights",
                "disposal_withdrawal_transfer",
                "retirement_or_recapture",
                "ltf_carryforward",
            ),
            "false",
        ),
    }
