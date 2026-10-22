"""Frozen candidate output and exact replay against accepted upstream inputs."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.calculation.models import TaxState
from tax_gps.candidate.activation import ActivatedAllocationPolicy
from tax_gps.candidate.engine import CANDIDATE_ENGINE_VERSION, build_candidates
from tax_gps.candidate.models import CandidateResult
from tax_gps.core.canonical import JsonValue, freeze
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.financial.models import GuardrailResult
from tax_gps.financial.state import FinancialState


@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    input_hash: str
    policy_hash: str
    engine_version: str
    output: JsonValue
    result_hash: str


def create_candidate_snapshot(result: CandidateResult) -> CandidateSnapshot:
    return CandidateSnapshot(
        result.input_hash,
        result.policy_hash,
        result.engine_version,
        freeze(result.to_dict()),
        result.result_hash,
    )


def replay_candidates(  # noqa: PLR0917 - snapshot and five accepted upstream inputs
    snapshot: CandidateSnapshot,
    tax: TaxState,
    discovery: DiscoveryResult,
    financial: FinancialState,
    guardrails: GuardrailResult,
    policy: ActivatedAllocationPolicy,
    *,
    engine_version: str = CANDIDATE_ENGINE_VERSION,
) -> CandidateResult:
    result = build_candidates(
        tax, discovery, financial, guardrails, policy, engine_version=engine_version
    )
    if (
        snapshot.input_hash != result.input_hash
        or snapshot.policy_hash != result.policy_hash
        or snapshot.engine_version != result.engine_version
        or snapshot.result_hash != result.result_hash
        or snapshot.output != freeze(result.to_dict())
    ):
        raise ValueError("candidate replay mismatch")
    return result
