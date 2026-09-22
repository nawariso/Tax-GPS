"""Immutable GuardrailSnapshot and deterministic replay verification (TGPS-P1-003 §52-53)."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.core.canonical import JsonValue, freeze
from tax_gps.core.errors import TaxCoreError
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.financial.engine import GUARDRAIL_ENGINE_VERSION, evaluate_guardrails
from tax_gps.financial.models import GuardrailResult
from tax_gps.financial.policy import ActivatedFinancialPolicy
from tax_gps.financial.profile import FinancialPlanningContext
from tax_gps.financial.state import (
    FinancialState,
    FinancialStateIntegrityError,
    verify_financial_state_integrity,
)


class GuardrailReplayError(TaxCoreError):
    """Replay inputs or output differ from the immutable guardrail snapshot."""


@dataclass(frozen=True, slots=True)
class GuardrailSnapshot:
    profile_hash: str
    discovery_hash: str
    financial_state_hash: str

    financial_policy_id: str
    financial_policy_version: str
    financial_policy_hash: str

    planning_date: str
    available_budget: str

    guardrail_engine_version: str

    guardrail_output: JsonValue
    guardrail_hash: str


def create_guardrail_snapshot(
    discovery: DiscoveryResult,
    state: FinancialState,
    activated_policy: ActivatedFinancialPolicy,
    context: FinancialPlanningContext,
    result: GuardrailResult,
) -> GuardrailSnapshot:
    if result.guardrail_hash == "":
        raise ValueError("guardrail result must be hashed")
    try:
        verify_financial_state_integrity(state)
    except FinancialStateIntegrityError as exc:
        raise ValueError(f"financial state failed self-integrity verification: {exc}") from exc
    if (
        result.profile_hash != discovery.profile_hash
        or result.discovery_hash != discovery.discovery_hash
        or result.financial_state_hash != state.state_hash
        or result.financial_policy_hash != activated_policy.content_hash
        or result.planning_date != context.planning_date
        or result.available_budget != context.available_budget
    ):
        raise ValueError("guardrail result does not match snapshot inputs")
    return GuardrailSnapshot(
        profile_hash=discovery.profile_hash,
        discovery_hash=discovery.discovery_hash,
        financial_state_hash=state.state_hash,
        financial_policy_id=activated_policy.policy_id,
        financial_policy_version=activated_policy.version,
        financial_policy_hash=activated_policy.content_hash,
        planning_date=context.planning_date.isoformat(),
        available_budget=context.available_budget.canonical(),
        guardrail_engine_version=result.engine_version,
        guardrail_output=freeze(result.to_dict()),
        guardrail_hash=result.guardrail_hash,
    )


def replay_guardrails(
    snapshot: GuardrailSnapshot,
    discovery: DiscoveryResult,
    state: FinancialState,
    activated_policy: ActivatedFinancialPolicy,
    context: FinancialPlanningContext,
    *,
    engine_version: str = GUARDRAIL_ENGINE_VERSION,
) -> GuardrailResult:
    if snapshot.profile_hash != discovery.profile_hash:
        raise GuardrailReplayError("profile does not match guardrail snapshot")
    if snapshot.discovery_hash != discovery.discovery_hash:
        raise GuardrailReplayError("discovery result does not match guardrail snapshot")
    try:
        verify_financial_state_integrity(state)
    except FinancialStateIntegrityError as exc:
        raise GuardrailReplayError(
            f"financial state failed self-integrity verification: {exc}"
        ) from exc
    if snapshot.financial_state_hash != state.state_hash:
        raise GuardrailReplayError("financial state does not match guardrail snapshot")
    if (
        snapshot.financial_policy_id != activated_policy.policy_id
        or snapshot.financial_policy_version != activated_policy.version
        or snapshot.financial_policy_hash != activated_policy.content_hash
    ):
        raise GuardrailReplayError("financial policy does not match guardrail snapshot")
    if (
        snapshot.planning_date != context.planning_date.isoformat()
        or snapshot.available_budget != context.available_budget.canonical()
    ):
        raise GuardrailReplayError("planning context does not match guardrail snapshot")
    if snapshot.guardrail_engine_version != engine_version:
        raise GuardrailReplayError("engine version does not match guardrail snapshot")
    result = evaluate_guardrails(
        discovery,
        state,
        activated_policy,
        context,
        engine_version=engine_version,
    )
    if snapshot.guardrail_hash != result.guardrail_hash:
        raise GuardrailReplayError("guardrail output hash does not match replay")
    if snapshot.guardrail_output != freeze(result.to_dict()):
        raise GuardrailReplayError("guardrail output does not match replay")
    return result
