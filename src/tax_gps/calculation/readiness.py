"""Pure baseline coverage decision; capacity facts do not authorize deductions."""

from dataclasses import dataclass, fields

from tax_gps.calculation.models import TaxStatus
from tax_gps.calculation.pvd import pvd_parameter
from tax_gps.calculation.rmf import assess_rmf
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import UserProfile, parent_eligibility_fact_id
from tax_gps.profile.pvd import PvdWageBasisError


@dataclass(frozen=True, slots=True)
class BaselineReadiness:
    status: TaxStatus
    reason_codes: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]


def assess_baseline(profile: UserProfile, *, pack: ActivatedRulePack) -> BaselineReadiness:  # noqa: PLR0912, PLR0915
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
    c02_unsupported = False
    c02_missing_start = len(missing)
    for group in ("other_rights", "fund_history"):
        facts = getattr(profile.benefits, group)
        if facts is None:
            missing.append(group)
        else:
            for item in fields(facts):
                value = getattr(facts, item.name)
                if value is None:
                    missing.append(f"{group}.{item.name}")
                elif value and not (group == "other_rights" and item.name == "rmf"):
                    reasons.append(f"{group.upper()}_{item.name.upper()}_UNSUPPORTED")
                    c02_unsupported = True
    pvd = profile.benefits.pvd
    if pvd is None or pvd.employee_paid is None:
        missing.append("pvd.employee_paid")
    elif pvd.employee_paid.is_positive():
        for item in fields(pvd):
            if item.name == "employee_paid":
                continue
            value = getattr(pvd, item.name)
            if value is None:
                missing.append(f"pvd.{item.name}")
            elif value is False:
                reasons.append(f"PVD_{item.name.upper()}_UNSUPPORTED")
                c02_unsupported = True
        if pvd.wage_basis is not None:
            if pvd.wage_basis == Money.zero() or pvd.wage_basis > profile.income.section_40_1:
                raise PvdWageBasisError
            minimum = Percentage.of(pvd_parameter(pack, "PVD_NORMAL_SCOPE", "minimum_rate"))
            maximum = Percentage.of(pvd_parameter(pack, "PVD_NORMAL_SCOPE", "maximum_rate"))
            if not pvd.wage_basis * minimum <= pvd.employee_paid <= pvd.wage_basis * maximum:
                reasons.append("PVD_RATE_OUTSIDE_NORMAL_SCOPE")
                c02_unsupported = True
    presence = (
        profile.benefits.other_rights.rmf if profile.benefits.other_rights is not None else None
    )
    combined = (
        presence is True
        and pvd is not None
        and pvd.employee_paid is not None
        and pvd.employee_paid.is_positive()
    )
    if combined:
        reasons.append("PVD_RMF_COMBINED_UNSUPPORTED")
        c02_unsupported = True
    else:
        rmf_reasons, rmf_missing = assess_rmf(
            presence, profile.benefits.rmf, profile.tax_year, pack
        )
        reasons.extend(rmf_reasons)
        missing.extend(rmf_missing)
        c02_unsupported = c02_unsupported or bool(rmf_reasons)
    if len(missing) > c02_missing_start:
        reasons.append("C02A_FACTS_REQUIRED")
    if unsupported_income:
        status = TaxStatus.ADVANCED_TAX_PATH_REQUIRED
    elif retirement or prior_usage or c02_unsupported:
        status = TaxStatus.UNSUPPORTED
    elif missing:
        status = TaxStatus.REQUIRES_INPUT
    else:
        status = TaxStatus.READY
    return BaselineReadiness(status, tuple(reasons), tuple(missing))
