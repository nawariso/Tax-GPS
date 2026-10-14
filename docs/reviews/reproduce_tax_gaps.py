"""Print synthetic review observations; does not certify tax eligibility or modify data.

Run from the repository root: python -m docs.reviews.reproduce_tax_gaps
"""

import json
from dataclasses import replace
from datetime import date

from examples.web_demo import calculate

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.engine import calculate_tax
from tax_gps.opportunity.activation import activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, load_bundled_rule_pack
from tax_gps.profile.models import (
    ExistingTaxBenefits,
    IncomeProfile,
    OpportunityFacts,
    Parent,
    RetirementContribution,
    UserProfile,
)


def main() -> None:
    pack = activate_rule_pack(load_bundled_rule_pack(BUNDLED_PACK_ID_2026))
    catalog = activate_catalog(load_bundled_catalog())
    profile = UserProfile(opportunity_facts=OpportunityFacts(shared_limit_usage=()),
        profile_id="synthetic-review",
        version="1",
        tax_year=TaxYear(2026),
        income=IncomeProfile(Money.of(990500)),
        benefits=ExistingTaxBenefits(social_security_paid=Money.of(10500)),
    )
    baseline = calculate_tax(profile, pack)
    retirement = calculate_tax(
        replace(
            profile,
            benefits=replace(
                profile.benefits,
                retirement_contributions=(RetirementContribution("RMF", Money.of(100000)),),
            ),
        ),
        pack,
    )
    unknown_parent = replace(
        profile, benefits=replace(profile.benefits, parents=(Parent("father", None),))
    )
    parent_tax = calculate_tax(unknown_parent, pack)
    parent_discovery = discover_opportunities(
        unknown_parent,
        parent_tax,
        pack,
        catalog,
        DiscoveryContext(TaxYear(2026), date(2026, 10, 15)),
    )
    demo = calculate(
        {
            "salary": "990500",
            "social_security": "10500",
            "assets": "500000",
            "expenses": "50000",
            "budget": "100000",
            "shared_usage": "100000",
            "planning_date": "2026-10-15",
        }
    )
    keys = ("status", "taxable_income", "pit")
    print(  # noqa: T201 - explicit diagnostic output using synthetic facts only
        json.dumps(
            {
                "baseline": {key: baseline.to_dict()[key] for key in keys},
                "retirement_usage_100000": {key: retirement.to_dict()[key] for key in keys},
                "unknown_parent_tax": {key: parent_tax.to_dict()[key] for key in keys},
                "unknown_parent_rights": [r.to_dict() for r in parent_discovery.existing_rights],
                "demo_shared_usage_100000": {
                    "tax_before": demo["tax_before"],
                    "outcomes": demo["outcomes"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
