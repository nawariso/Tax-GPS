"""Immutable audit snapshots and deterministic replay verification."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.calculation.models import TaxState
from tax_gps.core.canonical import JsonValue, freeze
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import ENGINE_VERSION, calculate_tax
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import UserProfile


class AuditReplayError(TaxCoreError):
    """Replay inputs or results differ from the immutable snapshot."""


@dataclass(frozen=True, slots=True)
class AuditSnapshot:
    profile_version: str
    profile_hash: str
    tax_year: TaxYear
    rule_pack_id: str
    rule_pack_version: str
    rule_pack_hash: str
    engine_version: str
    material_inputs: JsonValue
    calculated_outputs: JsonValue
    rules_applied: tuple[str, ...]
    calculation_trace: JsonValue
    output_hash: str


def create_audit_snapshot(
    profile: UserProfile, state: TaxState, pack: ActivatedRulePack
) -> AuditSnapshot:
    return AuditSnapshot(
        profile.version,
        profile.profile_hash(),
        profile.tax_year,
        pack.rule_pack_id,
        pack.version,
        pack.content_hash,
        state.engine_version,
        freeze(profile.to_dict()),
        freeze(state.material_dict()),
        state.rules_applied,
        freeze(state.calculation_trace.to_dict()),
        state.output_hash,
    )


def replay(
    snapshot: AuditSnapshot,
    profile: UserProfile,
    pack: ActivatedRulePack,
    *,
    engine_version: str = ENGINE_VERSION,
) -> TaxState:
    if (
        snapshot.profile_hash != profile.profile_hash()
        or snapshot.profile_version != profile.version
    ):
        raise AuditReplayError("profile snapshot does not match")
    if (
        snapshot.rule_pack_id != pack.rule_pack_id
        or snapshot.rule_pack_version != pack.version
        or snapshot.rule_pack_hash != pack.content_hash
    ):
        raise AuditReplayError("rule pack does not match")
    if snapshot.engine_version != engine_version:
        raise AuditReplayError("engine version does not match")
    state = calculate_tax(profile, pack, engine_version=engine_version)
    if snapshot.output_hash != state.output_hash:
        raise AuditReplayError("output hash does not match replay")
    return state
