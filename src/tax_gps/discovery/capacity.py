"""Opportunity Capacity decision boundary."""

from dataclasses import dataclass
from typing import cast

from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.opportunity.models import OpportunityCatalog, OpportunityDefinition


@dataclass(frozen=True, slots=True)
class OpportunityCapacity:
    standalone_limit: Money
    shared_limit_group: str | None
    shared_limit: Money | None
    shared_amount_used: Money
    remaining_capacity: Money

    def to_dict(self) -> dict[str, object]:
        return {
            "standalone_limit": self.standalone_limit.canonical(),
            "shared_limit_group": self.shared_limit_group,
            "shared_limit": self.shared_limit.canonical()
            if self.shared_limit is not None
            else None,
            "shared_amount_used": self.shared_amount_used.canonical(),
            "remaining_capacity": self.remaining_capacity.canonical(),
        }


def calculate_opportunity_capacity(
    definition: OpportunityDefinition,
    catalog: OpportunityCatalog,
    *,
    assessable_income: Money,
    shared_amount_used: Money,
) -> OpportunityCapacity:
    if definition.standalone_limit is None:
        raise ValueError("opportunity has no governed standalone limit")
    limit = definition.standalone_limit
    if definition.shared_limit_group is None:
        return OpportunityCapacity(limit, None, None, Money.zero(), limit)
    rule = catalog.rule(definition.rule_ids[0])
    rate = Percentage.of(cast(str, rule.parameters["assessable_income_rate"]))
    income_limit = assessable_income * rate
    shared_limit = Money.min(limit, income_limit)
    remaining = (shared_limit - shared_amount_used).floor_at_zero()
    return OpportunityCapacity(
        limit, definition.shared_limit_group, shared_limit, shared_amount_used, remaining
    )
