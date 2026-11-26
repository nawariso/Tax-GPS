# TGPS-P1-004 — Candidate Allocation & Outcome Engine

Status: implementation candidate, pending independent review
Base: `92bc65b7e5140807f86a0caecfbebb5f6cc8fb54`
Branch: `feature/tgps-p1-004-candidate-allocation-outcome`
Requirement: [`../requirements/TGPS-P1-004.md`](../requirements/TGPS-P1-004.md)

## Implementation and architecture

`src/tax_gps/candidate/models.py` defines frozen allocation-policy, shared-limit, deduction-treatment, allocation, outcome and result models. `engine.py` validates existing accepted input identities and readiness, constructs feasible compositions and uses `TaxState.tax_impact()` (the already accepted progressive PIT), preserving Decimal/Money semantics. `audit.py` freezes output and replays from accepted inputs. No new tax calculator, market data, ranking or recommendation layer was added. No modification to accepted P1-001/002/003 policy catalogs or their semantics.

Input direction is one-way: accepted `UserProfile`, core/catalog and tax/discovery/financial results feed activated candidate policy, then construction and audit replay. `AllocationPolicy` is raw data, never sufficient authority by its own hash. `candidate/activation.py` accepts only the exact bundled, EFFECTIVE opportunity catalog and versioned `TH-ALLOCATION-2026-001` policy shape for the matching tax year. A self-consistent `DiscoveryResult` hash is integrity metadata, not independent authority for remaining tax capacity. Activation binds `profile_hash` to discovery, replays the P1-002 discovery from the accepted profile, tax state, tax rule pack and catalog at the same planning date, compares replay hash and material content, and separately reuses P1-002 `calculate_opportunity_capacity` with the governed cap, income rate, accepted assessable income and accepted profile shared usage. The policy factory performs the same verification before deriving shared remaining capacity. Unknown shared usage cannot produce an allocatable candidate; rehashed, inflated capacity fails closed. It verifies full-allocation tax saving at governed capacity against `TaxState.tax_impact`. Activated evidence carries profile, discovery, tax, catalog and policy hashes plus rule/source IDs; snapshots store hashes, not raw profile facts. The only supported treatment is `FULL_ALLOCATION_DEDUCTION`; arbitrary percentages and all non-1:1 semantics are deferred until independently authorized upstream rules. Only one accepted allocatable opportunity currently belongs to the Thai ESG shared pool; general multi-member group activation fails closed. Synthetic multi-opportunity fixtures use a private construction helper, not production activation.

## Construction and outcomes

Candidate ID is SHA-256 over canonical sorted allocation JSON. NO_ACTION is first. Positive amounts come from the intersection of independent guardrail ceilings, budget, known spendable surplus, declared shared-group remainder, and the residual required to fund a subsequent opportunity at its own ceiling. Group usage is cumulative across opportunities, never independent. Empty and duplicate construction paths cannot inflate candidate count. Policy maximum is between 1 and 256; more than eight allocatable opportunities fails
before construction, and candidate-count overflow fails without returning any candidates. Non-baseline ordering is canonical allocation bytes, not economic desirability.

Every candidate records cash allocated, explicit deductible amount, progressive tax before/after/saved, cash outflow, unused budget, remaining spendable surplus, unchanged/unknown protection gap, stable reason codes, source hashes and engine version. Tax refunds are not assumed available as current cash. Existing rights remain in TaxState and do not consume new allocation budget. Partial financial state emits only the ordinary zero-allocation outcome, preserving unknown financial values. Baseline is calculated through the same tax impact path with zero deduction.

## Evidence and quality

Acceptance tests in `tests/acceptance/test_candidates.py`, `test_candidate_policy_binding.py` and `test_candidate_capacity_authority.py` cover exact employee PIT (THB 79,000 before, THB 60,500 after THB 100,000 full deduction), NO_ACTION, zero budget, zero tax benefit, CAP, synthetic-only shared collisions, satang boundaries, known/unknown protection, forged upstream and policy material, governed income/cap capacity, non-zero and unknown shared usage, the 297,150-to-300,000 self-rehashed forgery, overflow, canonical ordering, immutable policy and activated replay. The full local suite produced 608 passed, 100.00% statement and branch coverage. `ruff check`, `ruff format --check`, `mypy --strict`, and `uv build` passed locally. R1 was additive to 59c769c; R2 is additive to 7b7cce7. The engine contract remains `tax-gps-candidates/0.2.0`: R2 tightens authority verification but does not change accepted canonical candidate material or IDs. Historical snapshots require their version-matched engine. PR #3 remains open; exact R2-SHA CI and independent acceptance are pending at commit time.

## Requirement coverage and deferred scope

- Candidate construction, bounds, identity, deduplication and ordering: `candidate/engine.py`, `candidate/models.py`, acceptance tests.
- Budget, per-opportunity, shared, financial and eligibility gates: `engine.py::_verify_inputs`, `_allocatable`, `build_candidates` with bounded group accounting.
- Tax and financial outcomes: `engine.py::_outcome`, activated `FULL_ALLOCATION_DEDUCTION`, existing `TaxState.tax_impact` and Money.
- Audit/replay: `candidate/audit.py`, hash/material serialization, replay tests.
- Explicit exclusions: no winner selection, optimizer, product score, return model, market service, or forward projection.

R2 authority boundary: a self-consistent discovery hash is integrity metadata, not capacity authority. Production activation derives capacity from accepted profile usage facts, TaxState and the governed catalog by replaying P1-002 discovery and reusing its capacity function; no caller-edited remaining amount becomes a shared limit. R1 protections remain: full-deduction tax saving and rule/source/catalog provenance are checked, raw allocation policy is rejected by the production engine, and generalized multi-opportunity shared groups fail closed. Synthetic group mechanics are exercised only through a private test helper. No ranking or comparison is implemented.

PR #3: open; exact R2-SHA CI: pending until push; independent acceptance: pending; merge: not authorized.
