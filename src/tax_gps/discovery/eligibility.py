"""Opportunity Eligibility decision boundary."""

from dataclasses import dataclass
from enum import StrEnum


class EligibilityDecision(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INSUFFICIENT_FACTS = "INSUFFICIENT_FACTS"


@dataclass(frozen=True, slots=True)
class EligibilityFact:
    fact_id: str
    value: bool | None


@dataclass(frozen=True, slots=True)
class EligibilityAssessment:
    decision: EligibilityDecision
    failed_fact_ids: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]


def assess_eligibility(facts: tuple[EligibilityFact, ...]) -> EligibilityAssessment:
    failed = tuple(fact.fact_id for fact in facts if fact.value is False)
    missing = tuple(fact.fact_id for fact in facts if fact.value is None)
    if failed:
        return EligibilityAssessment(EligibilityDecision.INELIGIBLE, failed, missing)
    if missing:
        return EligibilityAssessment(EligibilityDecision.INSUFFICIENT_FACTS, (), missing)
    return EligibilityAssessment(EligibilityDecision.ELIGIBLE, (), ())
