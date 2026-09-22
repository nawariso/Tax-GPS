"""Unit tests for GuardrailSnapshot creation and deterministic replay (TGPS-P1-003 §52-53).

Every rejection path is exercised with a genuine mismatch and the specific error/message is
asserted, not merely executed.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.models import DiscoveryResult
from tax_gps.financial.audit import (
    GuardrailReplayError,
    create_guardrail_snapshot,
    replay_guardrails,
)
from tax_gps.financial.engine import evaluate_guardrails
from tax_gps.financial.models import GuardrailResult
from tax_gps.financial.policy import (
    ActivatedFinancialPolicy,
    activate_financial_policy,
    bundled_financial_policy,
)
from tax_gps.financial.profile import FinancialPlanningContext, FinancialProfile
from tax_gps.financial.state import FinancialState, compute_financial_state
from tests.acceptance.test_guardrails import _discovery, _tax_profile

PLANNING_DATE = date(2026, 6, 1)


def _policy() -> ActivatedFinancialPolicy:
    return activate_financial_policy(bundled_financial_policy(TaxYear(2026)))


def _fixture() -> tuple[
    DiscoveryResult,
    FinancialState,
    ActivatedFinancialPolicy,
    FinancialPlanningContext,
    GuardrailResult,
]:
    discovery = _discovery(_tax_profile(800000))
    profile = FinancialProfile(
        liquid_assets=Money.of(500000), monthly_essential_expenses=Money.of(50000)
    )
    policy = _policy()
    context = FinancialPlanningContext(planning_date=PLANNING_DATE, available_budget=Money.of(0))
    state = compute_financial_state(profile, policy, context)
    result = evaluate_guardrails(discovery, state, policy, context)
    return discovery, state, policy, context, result


def test_create_snapshot_round_trips_and_replays() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    replayed = replay_guardrails(snapshot, discovery, state, policy, context)
    assert replayed.guardrail_hash == result.guardrail_hash
    assert replayed.to_dict() == result.to_dict()


def test_create_snapshot_rejects_unhashed_result() -> None:
    discovery, state, policy, context, result = _fixture()
    unhashed = replace(result, guardrail_hash="")
    with pytest.raises(ValueError, match="must be hashed"):
        create_guardrail_snapshot(discovery, state, policy, context, unhashed)


def test_create_snapshot_rejects_profile_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, profile_hash="deadbeef")
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_create_snapshot_rejects_discovery_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, discovery_hash="deadbeef")
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_create_snapshot_rejects_financial_state_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, financial_state_hash="deadbeef")
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_create_snapshot_rejects_financial_policy_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, financial_policy_hash="deadbeef")
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_create_snapshot_rejects_planning_date_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, planning_date=date(2026, 7, 1))
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_create_snapshot_rejects_available_budget_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    mismatched = replace(result, available_budget=Money.of(999))
    with pytest.raises(ValueError, match="does not match snapshot inputs"):
        create_guardrail_snapshot(discovery, state, policy, context, mismatched)


def test_replay_rejects_profile_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, profile_hash="deadbeef")
    with pytest.raises(GuardrailReplayError, match="profile does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_discovery_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, discovery_hash="deadbeef")
    with pytest.raises(GuardrailReplayError, match="discovery result does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_financial_state_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, financial_state_hash="deadbeef")
    with pytest.raises(GuardrailReplayError, match="financial state does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_financial_policy_id_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, financial_policy_id="OTHER-POLICY")
    with pytest.raises(GuardrailReplayError, match="financial policy does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_financial_policy_version_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, financial_policy_version="9.9.9")
    with pytest.raises(GuardrailReplayError, match="financial policy does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_financial_policy_hash_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, financial_policy_hash="deadbeef")
    with pytest.raises(GuardrailReplayError, match="financial policy does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_planning_date_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, planning_date=date(2026, 7, 1).isoformat())
    with pytest.raises(GuardrailReplayError, match="planning context does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_available_budget_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, available_budget=Money.of(999).canonical())
    with pytest.raises(GuardrailReplayError, match="planning context does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_engine_version_mismatch() -> None:
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    stale_snapshot = replace(snapshot, guardrail_engine_version="other-engine/9.9.9")
    with pytest.raises(GuardrailReplayError, match="engine version does not match"):
        replay_guardrails(stale_snapshot, discovery, state, policy, context)


def test_replay_rejects_guardrail_hash_mismatch_after_recomputation() -> None:
    """A snapshot claiming a hash the live re-evaluation does not reproduce must fail closed."""
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    tampered_snapshot = replace(snapshot, guardrail_hash="deadbeef")
    with pytest.raises(GuardrailReplayError, match="guardrail output hash does not match"):
        replay_guardrails(tampered_snapshot, discovery, state, policy, context)


def test_replay_rejects_guardrail_output_mismatch_with_matching_hash() -> None:
    """Belt-and-braces: even if a forged hash collided, the frozen output must also match."""
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    tampered_snapshot = replace(snapshot, guardrail_output={"forged": True})
    with pytest.raises(GuardrailReplayError, match="guardrail output does not match replay"):
        replay_guardrails(tampered_snapshot, discovery, state, policy, context)


# --- R1-02: FinancialState self-integrity verified at both trust boundaries ----------------


def test_create_snapshot_rejects_tampered_financial_state_with_stale_hash() -> None:
    """Snapshot creation must not trust ``state.state_hash`` at face value: a state mutated
    after computation, with its carried hash left stale, fails closed even though nothing
    about the ``GuardrailResult`` inputs it is compared against changed.
    """
    discovery, state, policy, context, result = _fixture()
    tampered_state = replace(state, liquid_assets=Money.of(999999999))
    with pytest.raises(ValueError, match="failed self-integrity verification"):
        create_guardrail_snapshot(discovery, tampered_state, policy, context, result)


def test_replay_rejects_tampered_financial_state_with_stale_hash() -> None:
    """Replay must not trust ``state.state_hash`` at face value either: this is the second
    of the two required trust boundaries (R1-02).
    """
    discovery, state, policy, context, result = _fixture()
    snapshot = create_guardrail_snapshot(discovery, state, policy, context, result)
    tampered_state = replace(state, liquid_assets=Money.of(999999999))
    with pytest.raises(GuardrailReplayError, match="failed self-integrity verification"):
        replay_guardrails(snapshot, discovery, tampered_state, policy, context)
