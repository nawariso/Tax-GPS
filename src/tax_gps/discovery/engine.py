"""Application service for deterministic existing-right and opportunity discovery."""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from tax_gps.calculation.models import TaxState, TaxStatus
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.capacity import calculate_opportunity_capacity
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.effective_period import EffectivePeriodOutcome, check_effective_period
from tax_gps.discovery.eligibility import EligibilityDecision, assess_eligibility
from tax_gps.discovery.facts import collect_facts
from tax_gps.discovery.intent import IntentOutcome, check_intrinsic_intent
from tax_gps.discovery.models import (
    DiscoveredOpportunity,
    DiscoveredRight,
    DiscoveryReasonCode,
    DiscoveryResult,
    DiscoveryStatus,
)
from tax_gps.engine import calculate_tax
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.opportunity.models import (
    OpportunityDefinition,
    OpportunityStatus,
    OpportunityType,
)
from tax_gps.opportunity.readiness import evaluate_opportunity_readiness
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource
from tax_gps.profile.models import UserProfile

DISCOVERY_ENGINE_VERSION = "tax-gps-discovery/0.2.0"
T = TypeVar("T")


def _dedupe(values: tuple[T, ...]) -> tuple[T, ...]:  # noqa: UP047
    result: list[T] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


def _source_ids_for(
    definition: OpportunityDefinition,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
) -> tuple[str, ...]:
    result: list[str] = list(definition.source_ids)
    for rule_id in definition.rule_ids:
        rule = (
            pack.pack.find_rule(rule_id)
            if definition.opportunity_type is OpportunityType.EXISTING_RIGHT
            else catalog.catalog.find_rule(rule_id)
        )
        if rule is not None and rule.source_id is not None:
            result.append(rule.source_id)
            result.extend(rule.supplementary_source_ids)
    return _dedupe(tuple(result))


def _existing_rights(
    profile: UserProfile,
    state: TaxState,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    context: DiscoveryContext,
) -> tuple[DiscoveredRight, ...]:
    benefits = profile.benefits
    amount_by_id = {
        opportunity_ids.PERSONAL_ALLOWANCE: state.allowances.personal,
        opportunity_ids.PARENT_ALLOWANCE: state.allowances.parents,
        opportunity_ids.CHILD_ALLOWANCE: state.allowances.children,
        opportunity_ids.SOCIAL_SECURITY: state.allowances.social_security,
        opportunity_ids.MORTGAGE_INTEREST: state.allowances.mortgage_interest,
    }
    present = {
        opportunity_ids.PERSONAL_ALLOWANCE: state.allowances.personal.is_positive(),
        opportunity_ids.PARENT_ALLOWANCE: bool(benefits.parents)
        and any(parent.eligible is not False for parent in benefits.parents),
        opportunity_ids.CHILD_ALLOWANCE: state.allowances.children.is_positive(),
        opportunity_ids.SOCIAL_SECURITY: state.allowances.social_security.is_positive(),
        opportunity_ids.MORTGAGE_INTEREST: state.allowances.mortgage_interest.is_positive(),
        opportunity_ids.RETIREMENT_SHARED_CAPACITY: bool(benefits.retirement_contributions),
    }
    rights: list[DiscoveredRight] = []
    for right_id in opportunity_ids.EXISTING_RIGHT_IDS:
        if not present[right_id]:
            continue
        definition = catalog.catalog.definition(right_id)
        missing: tuple[str, ...] = ()
        status = OpportunityStatus.AVAILABLE
        reasons: tuple[DiscoveryReasonCode, ...] = (DiscoveryReasonCode.EXISTING_RIGHT_AVAILABLE,)
        readiness = evaluate_opportunity_readiness(
            definition,
            catalog.catalog,
            pack,
            planning_date=context.planning_date,
        )
        if not readiness.ready:
            status = OpportunityStatus.RULE_NOT_READY
            reasons = (DiscoveryReasonCode.RULE_NOT_READY,)
        elif check_effective_period(definition, context) is EffectivePeriodOutcome.OUTSIDE_PERIOD:
            status = OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD
            reasons = (DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD,)
        elif right_id == opportunity_ids.PARENT_ALLOWANCE:
            missing = tuple(
                f"parent.{parent.relationship}.eligible"
                for parent in benefits.parents
                if parent.eligible is None
            )
            if missing:
                status = OpportunityStatus.REQUIRES_INPUT
                reasons = (DiscoveryReasonCode.REQUIRES_INPUT,)
        remaining: Money | None = None
        if right_id == opportunity_ids.RETIREMENT_SHARED_CAPACITY:
            claimed = Money.sum(item.amount_used for item in benefits.retirement_contributions)
            remaining = next(
                (
                    capacity.usable_amount
                    for capacity in state.deduction_capacities
                    if capacity.shared_group == definition.shared_limit_group
                ),
                Money.zero(),
            )
            if remaining.is_zero():
                reasons += (DiscoveryReasonCode.NO_REMAINING_CAPACITY,)
        else:
            claimed = amount_by_id[right_id]
        rights.append(
            DiscoveredRight(
                right_id=right_id,
                name=definition.name,
                category=definition.category,
                opportunity_type=OpportunityType.EXISTING_RIGHT,
                status=status,
                requires_new_cash=False,
                claimed_amount=claimed,
                remaining_capacity=remaining,
                tax_impact=None,
                rule_ids=definition.rule_ids,
                source_ids=_source_ids_for(definition, pack, catalog),
                reason_codes=reasons,
                missing_fact_ids=missing,
            )
        )
    return tuple(rights)


def _discovered_opportunity(
    definition: OpportunityDefinition,
    source_ids: tuple[str, ...],
    *,
    status: OpportunityStatus,
    remaining_capacity: Money | None,
    maximum_tax_saving: Money | None,
    reason_codes: tuple[DiscoveryReasonCode, ...],
    missing_fact_ids: tuple[str, ...] = (),
    failed_fact_ids: tuple[str, ...] = (),
) -> DiscoveredOpportunity:
    return DiscoveredOpportunity(
        opportunity_id=definition.opportunity_id,
        name=definition.name,
        category=definition.category,
        opportunity_type=definition.opportunity_type,
        status=status,
        requires_new_cash=definition.requires_new_cash,
        intrinsic_need_required=definition.intrinsic_need_required,
        remaining_capacity=remaining_capacity,
        maximum_tax_saving_at_capacity=maximum_tax_saving,
        shared_limit_group=definition.shared_limit_group,
        lockup_metadata=definition.lockup_metadata,
        evidence_requirements=definition.evidence_requirements,
        rule_ids=definition.rule_ids,
        source_ids=source_ids,
        reason_codes=reason_codes,
        missing_fact_ids=missing_fact_ids,
        failed_fact_ids=failed_fact_ids,
    )


def _opportunity(  # noqa: PLR0911, PLR0917
    definition: OpportunityDefinition,
    profile: UserProfile,
    state: TaxState,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    context: DiscoveryContext,
) -> DiscoveredOpportunity:
    source_ids = _source_ids_for(definition, pack, catalog)
    facts = collect_facts(definition, profile)
    intent = check_intrinsic_intent(definition, facts.intent)
    if intent is IntentOutcome.NOT_INTENDED:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.INELIGIBLE,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.NO_INTRINSIC_NEED,),
        )
    if not evaluate_opportunity_readiness(
        definition,
        catalog.catalog,
        pack,
        planning_date=context.planning_date,
    ).ready:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.RULE_NOT_READY,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.RULE_NOT_READY,),
        )
    if check_effective_period(definition, context) is EffectivePeriodOutcome.OUTSIDE_PERIOD:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.OUTSIDE_EFFECTIVE_PERIOD,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.OUTSIDE_EFFECTIVE_PERIOD,),
        )
    if intent is IntentOutcome.UNKNOWN:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.REQUIRES_INPUT,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.REQUIRES_INPUT,),
            missing_fact_ids=(facts.intent.fact_id,),
        )
    assessment = assess_eligibility(facts.conditions)
    if assessment.decision is EligibilityDecision.INELIGIBLE:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.INELIGIBLE,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.ELIGIBILITY_CONDITION_FAILED,),
            missing_fact_ids=assessment.missing_fact_ids,
            failed_fact_ids=assessment.failed_fact_ids,
        )
    if assessment.decision is EligibilityDecision.INSUFFICIENT_FACTS:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.REQUIRES_INPUT,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.REQUIRES_INPUT,),
            missing_fact_ids=assessment.missing_fact_ids,
        )
    shared_used = profile.opportunity_facts.shared_limit_amount_used(definition.shared_limit_group)
    if shared_used is None:
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.REQUIRES_INPUT,
            remaining_capacity=None,
            maximum_tax_saving=None,
            reason_codes=(DiscoveryReasonCode.REQUIRES_INPUT,),
            missing_fact_ids=(f"shared_limit_usage.{definition.shared_limit_group}",),
        )
    capacity = calculate_opportunity_capacity(
        definition,
        catalog.catalog,
        assessable_income=state.income.assessable_income,
        shared_amount_used=shared_used,
    )
    if capacity.remaining_capacity.is_zero():
        reasons = [DiscoveryReasonCode.NO_REMAINING_CAPACITY]
        if definition.shared_limit_group is not None and shared_used.is_positive():
            reasons.append(DiscoveryReasonCode.SHARED_LIMIT_APPLIED)
        return _discovered_opportunity(
            definition,
            source_ids,
            status=OpportunityStatus.INELIGIBLE,
            remaining_capacity=Money.zero(),
            maximum_tax_saving=Money.zero(),
            reason_codes=tuple(reasons),
        )
    tax_saving = state.tax_impact(capacity.remaining_capacity).saving
    reasons = [DiscoveryReasonCode.ELIGIBLE_OPPORTUNITY]
    if definition.shared_limit_group is not None and shared_used.is_positive():
        reasons.append(DiscoveryReasonCode.SHARED_LIMIT_APPLIED)
    if tax_saving.is_zero():
        reasons.append(DiscoveryReasonCode.ZERO_CURRENT_TAX_BENEFIT)
    return _discovered_opportunity(
        definition,
        source_ids,
        status=OpportunityStatus.AVAILABLE,
        remaining_capacity=capacity.remaining_capacity,
        maximum_tax_saving=tax_saving,
        reason_codes=tuple(reasons),
    )


def _resolve_sources(
    source_ids: tuple[str, ...], pack: ActivatedRulePack, catalog: ActivatedOpportunityCatalog
) -> tuple[RuleSource, ...]:
    result: list[RuleSource] = []
    for source_id in source_ids:
        catalog_source = catalog.catalog.find_source(source_id)
        pack_source = pack.pack.find_source(source_id)
        source = (
            None
            if catalog_source is not None
            and pack_source is not None
            and catalog_source != pack_source
            else catalog_source or pack_source
        )
        if source is not None and source not in result:
            result.append(source)
    return tuple(result)


def discover_opportunities(
    profile: UserProfile,
    state: TaxState,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    context: DiscoveryContext,
    *,
    engine_version: str = DISCOVERY_ENGINE_VERSION,
) -> DiscoveryResult:
    years = {
        profile.tax_year,
        state.tax_year,
        pack.pack.tax_year,
        catalog.catalog.tax_year,
        context.tax_year,
    }
    if len(years) != 1:
        raise ValueError("profile, tax state, policy, catalog, and context tax years must match")
    expected_state = calculate_tax(profile, pack)
    if expected_state.output_hash != state.output_hash:
        raise ValueError("tax state does not match profile and activated policy")
    if state.status is not TaxStatus.READY:
        result = DiscoveryResult(
            status=DiscoveryStatus.UNSUPPORTED,
            profile_hash=profile.profile_hash(),
            tax_state_hash=state.output_hash,
            rule_pack_hash=pack.content_hash,
            opportunity_catalog_hash=catalog.content_hash,
            tax_year=context.tax_year.gregorian,
            planning_date=context.planning_date,
            existing_rights=(),
            opportunities=(),
            reason_codes=(DiscoveryReasonCode.UNSUPPORTED_TAX_STATE,),
            rules_applied=(),
            sources=(),
            catalog_version=catalog.version,
            engine_version=engine_version,
            discovery_hash="",
        )
        return _with_hash(result)
    rights = _existing_rights(profile, state, pack, catalog, context)
    opportunities = tuple(
        _opportunity(definition, profile, state, pack, catalog, context)
        for definition in catalog.catalog.definitions
        if definition.opportunity_type is OpportunityType.NEW_CASH
    )
    rules = _dedupe(
        tuple(rule for right in rights for rule in right.rule_ids)
        + tuple(rule for item in opportunities for rule in item.rule_ids)
    )
    source_ids = _dedupe(
        tuple(source for right in rights for source in right.source_ids)
        + tuple(source for item in opportunities for source in item.source_ids)
    )
    reasons = _dedupe(
        tuple(reason for right in rights for reason in right.reason_codes)
        + tuple(reason for item in opportunities for reason in item.reason_codes)
    )
    result = DiscoveryResult(
        status=DiscoveryStatus.READY,
        profile_hash=profile.profile_hash(),
        tax_state_hash=state.output_hash,
        rule_pack_hash=pack.content_hash,
        opportunity_catalog_hash=catalog.content_hash,
        tax_year=context.tax_year.gregorian,
        planning_date=context.planning_date,
        existing_rights=rights,
        opportunities=opportunities,
        reason_codes=reasons,
        rules_applied=rules,
        sources=_resolve_sources(source_ids, pack, catalog),
        catalog_version=catalog.version,
        engine_version=engine_version,
        discovery_hash="",
    )
    return _with_hash(result)


def _with_hash(result: DiscoveryResult) -> DiscoveryResult:
    return replace(result, discovery_hash=sha256_hex(canonical_json(result.material_dict())))
