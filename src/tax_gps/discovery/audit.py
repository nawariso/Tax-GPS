"""Immutable discovery snapshots and deterministic replay verification."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.calculation.models import TaxState
from tax_gps.core.canonical import JsonValue, freeze
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import (
    DISCOVERY_ENGINE_VERSION,
    discover_opportunities,
)
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import UserProfile


class DiscoveryReplayError(TaxCoreError):
    """Replay inputs or output differ from the immutable discovery snapshot."""


@dataclass(frozen=True, slots=True)
class DiscoverySnapshot:
    profile_hash: str
    tax_state_hash: str
    rule_pack_id: str
    rule_pack_version: str
    rule_pack_hash: str
    opportunity_catalog_version: str
    opportunity_catalog_hash: str
    discovery_engine_version: str
    tax_year: TaxYear
    planning_date: str
    discovery_output: JsonValue
    discovery_hash: str


def create_discovery_snapshot(  # noqa: PLR0917
    profile: UserProfile,
    state: TaxState,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    context: DiscoveryContext,
    result: DiscoveryResult,
) -> DiscoverySnapshot:
    if result.discovery_hash == "":
        raise ValueError("discovery result must be hashed")
    return DiscoverySnapshot(
        profile.profile_hash(),
        state.output_hash,
        pack.rule_pack_id,
        pack.version,
        pack.content_hash,
        catalog.version,
        catalog.content_hash,
        result.engine_version,
        context.tax_year,
        context.planning_date.isoformat(),
        freeze(result.to_dict()),
        result.discovery_hash,
    )


def replay_discovery(  # noqa: PLR0917
    snapshot: DiscoverySnapshot,
    profile: UserProfile,
    state: TaxState,
    pack: ActivatedRulePack,
    catalog: ActivatedOpportunityCatalog,
    context: DiscoveryContext,
    *,
    engine_version: str = DISCOVERY_ENGINE_VERSION,
) -> DiscoveryResult:
    if snapshot.profile_hash != profile.profile_hash():
        raise DiscoveryReplayError("profile does not match discovery snapshot")
    if snapshot.tax_state_hash != state.output_hash:
        raise DiscoveryReplayError("tax state does not match discovery snapshot")
    if (
        snapshot.rule_pack_id != pack.rule_pack_id
        or snapshot.rule_pack_version != pack.version
        or snapshot.rule_pack_hash != pack.content_hash
    ):
        raise DiscoveryReplayError("rule pack does not match discovery snapshot")
    if (
        snapshot.opportunity_catalog_version != catalog.version
        or snapshot.opportunity_catalog_hash != catalog.content_hash
    ):
        raise DiscoveryReplayError("catalog does not match discovery snapshot")
    if snapshot.discovery_engine_version != engine_version:
        raise DiscoveryReplayError("engine version does not match discovery snapshot")
    if (
        snapshot.tax_year != context.tax_year
        or snapshot.planning_date != context.planning_date.isoformat()
    ):
        raise DiscoveryReplayError("context does not match discovery snapshot")
    result = discover_opportunities(
        profile,
        state,
        pack,
        catalog,
        context,
        engine_version=engine_version,
    )
    if snapshot.discovery_hash != result.discovery_hash:
        raise DiscoveryReplayError("discovery output hash does not match replay")
    if snapshot.discovery_output != freeze(result.to_dict()):
        raise DiscoveryReplayError("discovery output does not match replay")
    return result
