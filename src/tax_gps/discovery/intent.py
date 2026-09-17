"""Intrinsic Intent Check decision boundary."""

from enum import StrEnum

from tax_gps.discovery.eligibility import EligibilityFact
from tax_gps.opportunity.models import OpportunityDefinition


class IntentOutcome(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    UNKNOWN = "UNKNOWN"
    NOT_INTENDED = "NOT_INTENDED"
    INTENDED = "INTENDED"


def check_intrinsic_intent(
    definition: OpportunityDefinition, intent: EligibilityFact
) -> IntentOutcome:
    if not definition.intrinsic_need_required:
        return IntentOutcome.NOT_REQUIRED
    if intent.value is None:
        return IntentOutcome.UNKNOWN
    return IntentOutcome.INTENDED if intent.value else IntentOutcome.NOT_INTENDED
