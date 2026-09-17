"""Effective Period Check decision boundary."""

from enum import StrEnum

from tax_gps.discovery.context import DiscoveryContext
from tax_gps.opportunity.models import OpportunityDefinition


class EffectivePeriodOutcome(StrEnum):
    WITHIN_PERIOD = "WITHIN_PERIOD"
    OUTSIDE_PERIOD = "OUTSIDE_PERIOD"


def check_effective_period(
    definition: OpportunityDefinition, context: DiscoveryContext
) -> EffectivePeriodOutcome:
    within = context.planning_date >= definition.effective_from and (
        definition.effective_to is None or context.planning_date <= definition.effective_to
    )
    return EffectivePeriodOutcome.WITHIN_PERIOD if within else EffectivePeriodOutcome.OUTSIDE_PERIOD
