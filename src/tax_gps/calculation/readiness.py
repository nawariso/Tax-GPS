"""Pure baseline coverage decision; capacity facts do not authorize deductions."""

from dataclasses import dataclass

from tax_gps.calculation.models import TaxStatus
from tax_gps.core.errors import InvalidValueError
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.profile.models import UserProfile, parent_eligibility_fact_id


@dataclass(frozen=True, slots=True)
class BaselineReadiness:
    status: TaxStatus
    reason_codes: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]


def assess_baseline(profile: UserProfile) -> BaselineReadiness:
    usage = profile.opportunity_facts.shared_limit_usage
    if usage is not None and any(item.group_id != THAI_ESG_2026_POOL for item in usage):
        raise InvalidValueError("unknown shared usage pool")
    reasons: list[str] = []
    missing: list[str] = []
    unsupported_income = any(item.amount.is_positive() for item in profile.income.unsupported)
    retirement = any(
        item.amount_used.is_positive() for item in profile.benefits.retirement_contributions
    )
    prior_usage = usage is not None and any(item.amount_used.is_positive() for item in usage)
    if unsupported_income:
        reasons.append("UNSUPPORTED_INCOME")
    if retirement:
        reasons.append("RETIREMENT_BASELINE_UNSUPPORTED")
    if prior_usage:
        reasons.append("PRIOR_SHARED_USAGE_BASELINE_UNSUPPORTED")
    unknown_parents = tuple(
        parent_eligibility_fact_id(parent.relationship, index)
        for index, parent in enumerate(profile.benefits.parents)
        if parent.eligible is None
    )
    if unknown_parents:
        reasons.append("PARENT_ELIGIBILITY_REQUIRED")
        missing.extend(unknown_parents)
    if usage is None:
        reasons.append("SHARED_USAGE_REQUIRED")
        missing.append("opportunity_facts.shared_limit_usage")
    if unsupported_income:
        status = TaxStatus.ADVANCED_TAX_PATH_REQUIRED
    elif retirement or prior_usage:
        status = TaxStatus.UNSUPPORTED
    elif missing:
        status = TaxStatus.REQUIRES_INPUT
    else:
        status = TaxStatus.READY
    return BaselineReadiness(status, tuple(reasons), tuple(missing))
