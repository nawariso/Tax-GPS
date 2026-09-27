"""Bind candidate deduction policy to the bundled, activated P1-002 catalog."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.calculation.models import TaxState, TaxStatus
from tax_gps.candidate.models import (
    AllocationPolicy,
    DeductionSemantics,
    OpportunityTreatment,
    SharedLimit,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.discovery.engine import _source_ids_for
from tax_gps.discovery.models import DiscoveryResult, DiscoveryStatus
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog, activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.opportunity.models import OpportunityStatus, OpportunityType
from tax_gps.opportunity.readiness import evaluate_opportunity_readiness
from tax_gps.policy.models import RuleStatus

BUNDLED_ALLOCATION_POLICY_ID = "TH-ALLOCATION-2026-001"
BUNDLED_ALLOCATION_POLICY_VERSION = "1.0.0"
BUNDLED_CANDIDATE_MAXIMUM = 32


@dataclass(frozen=True, slots=True)
class ActivatedAllocationPolicy:
    policy: AllocationPolicy
    catalog: ActivatedOpportunityCatalog
    content_hash: str
    discovery_hash: str
    tax_state_hash: str
    rule_ids: tuple[str, ...]
    source_ids: tuple[str, ...]

    @property
    def catalog_hash(self) -> str:
        return self.policy.catalog_hash


def _validate_upstream(
    tax: TaxState, discovery: DiscoveryResult, catalog: ActivatedOpportunityCatalog
) -> None:
    bundled = activate_catalog(load_bundled_catalog())
    if catalog.content_hash != bundled.content_hash or catalog != bundled:
        raise ValueError("allocation catalog is not the accepted bundled catalog")
    if discovery.opportunity_catalog_hash != catalog.content_hash:
        raise ValueError("allocation catalog hash differs from discovery")
    if discovery.discovery_hash != sha256_hex(canonical_json(discovery.material_dict())):
        raise ValueError("discovery integrity mismatch")
    if tax.output_hash != sha256_hex(canonical_json(tax.material_dict())):
        raise ValueError("tax state integrity mismatch")
    if (
        tax.status is not TaxStatus.READY
        or discovery.status is not DiscoveryStatus.READY
        or tax.output_hash != discovery.tax_state_hash
        or tax.tax_year.gregorian != discovery.tax_year
        or tax._activated_pack.content_hash != discovery.rule_pack_hash
    ):
        raise ValueError("candidate inputs do not match accepted tax/discovery state")


def _accepted_opportunities(
    tax: TaxState, discovery: DiscoveryResult, catalog: ActivatedOpportunityCatalog
) -> tuple[tuple[str, str | None, Money], ...]:
    _validate_upstream(tax, discovery, catalog)
    accepted: list[tuple[str, str | None, Money]] = []
    discovered_ids: set[str] = set()
    for item in discovery.opportunities:
        if item.opportunity_id in discovered_ids:
            raise ValueError("duplicate discovered opportunity")
        discovered_ids.add(item.opportunity_id)
        definition = catalog.catalog.find_definition(item.opportunity_id)
        if definition is None or definition.opportunity_type is not OpportunityType.NEW_CASH:
            raise ValueError("unknown opportunity in discovery")
        if (
            item.rule_ids != definition.rule_ids
            or item.source_ids != _source_ids_for(definition, tax._activated_pack, catalog)
            or item.shared_limit_group != definition.shared_limit_group
            or item.opportunity_type is not definition.opportunity_type
            or item.requires_new_cash != definition.requires_new_cash
        ):
            raise ValueError("discovery rule/source/group provenance mismatch")
        if item.status is not OpportunityStatus.AVAILABLE:
            continue
        if not evaluate_opportunity_readiness(
            definition, catalog.catalog, tax._activated_pack, planning_date=discovery.planning_date
        ).ready:
            raise ValueError("allocatable opportunity rule is not effective and ready")
        if (
            item.remaining_capacity is None
            or item.maximum_tax_saving_at_capacity is None
            or not item.requires_new_cash
        ):
            raise ValueError("allocatable opportunity has incomplete P1-002 tax semantics")
        if tax.tax_impact(item.remaining_capacity).saving != item.maximum_tax_saving_at_capacity:
            raise ValueError("P1-002 tax semantics disagree with full allocation deduction")
        accepted.append((item.opportunity_id, item.shared_limit_group, item.remaining_capacity))
    return tuple(accepted)


def _shared_groups(
    accepted: tuple[tuple[str, str | None, Money], ...],
) -> tuple[SharedLimit, ...]:
    groups: dict[str, list[Money]] = {}
    for _, group, capacity in accepted:
        if group is not None:
            groups.setdefault(group, []).append(capacity)
    if any(len(capacities) != 1 for capacities in groups.values()):
        raise ValueError("generalized multi-opportunity shared group is not governed")
    return tuple(SharedLimit(group, capacities[0]) for group, capacities in sorted(groups.items()))


def bundled_allocation_policy(
    tax: TaxState, discovery: DiscoveryResult, catalog: ActivatedOpportunityCatalog
) -> AllocationPolicy:
    """Construct the only production policy shape from accepted P1-002 facts."""
    accepted = _accepted_opportunities(tax, discovery, catalog)
    return AllocationPolicy(
        BUNDLED_ALLOCATION_POLICY_ID,
        catalog.content_hash,
        tuple(
            OpportunityTreatment(item_id, DeductionSemantics.FULL_ALLOCATION_DEDUCTION)
            for item_id, _, _ in accepted
        ),
        _shared_groups(accepted),
        BUNDLED_CANDIDATE_MAXIMUM,
        tax_year=discovery.tax_year,
        version=BUNDLED_ALLOCATION_POLICY_VERSION,
        status=RuleStatus.EFFECTIVE,
    )


def activate_allocation_policy(
    policy: AllocationPolicy,
    tax: TaxState,
    discovery: DiscoveryResult,
    catalog: ActivatedOpportunityCatalog,
) -> ActivatedAllocationPolicy:
    """Reject self-attested treatment/group values; bind to the accepted bundle."""
    accepted = _accepted_opportunities(tax, discovery, catalog)
    if policy.catalog_hash != discovery.opportunity_catalog_hash:
        raise ValueError("allocation policy catalog hash mismatch")
    if (
        policy.policy_id != BUNDLED_ALLOCATION_POLICY_ID
        or policy.version != BUNDLED_ALLOCATION_POLICY_VERSION
        or policy.tax_year != discovery.tax_year
    ):
        raise ValueError("allocation policy identity/version/tax year not accepted")
    if policy.status is not RuleStatus.EFFECTIVE:
        raise ValueError("allocation policy is not effective")
    known = {item_id for item_id, _, _ in accepted}
    provided = {item.opportunity_id for item in policy.treatments}
    if provided - known:
        raise ValueError("allocation treatment for unknown opportunity")
    if known - provided:
        raise ValueError("allocation policy omits treatment for allocatable opportunity")
    required_groups = {group for _, group, _ in accepted if group is not None}
    provided_groups = {item.group_id for item in policy.shared_limits}
    if provided_groups - required_groups:
        raise ValueError("allocation policy contains unknown shared group")
    if required_groups - provided_groups:
        raise ValueError("allocation policy omits shared group")
    expected = bundled_allocation_policy(tax, discovery, catalog)
    if any(
        item.remaining
        != next(
            required.remaining
            for required in expected.shared_limits
            if required.group_id == item.group_id
        )
        for item in policy.shared_limits
    ):
        raise ValueError("shared remaining disagrees with accepted P1-002 capacity")
    if policy.material_dict() != expected.material_dict():
        raise ValueError("allocation policy differs from accepted production contract")
    definitions = [catalog.catalog.definition(item_id) for item_id, _, _ in accepted]
    rule_ids = tuple(
        dict.fromkeys(rule for definition in definitions for rule in definition.rule_ids)
    )
    source_ids = tuple(
        dict.fromkeys(
            source
            for item in discovery.opportunities
            if item.opportunity_id in known
            for source in item.source_ids
        )
    )
    return ActivatedAllocationPolicy(
        policy,
        catalog,
        policy.content_hash(),
        discovery.discovery_hash,
        tax.output_hash,
        rule_ids,
        source_ids,
    )
