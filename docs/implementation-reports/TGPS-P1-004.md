# TGPS-P1-004 — Candidate Allocation & Outcome Engine

Status: implementation candidate, pending independent review
Base: `92bc65b7e5140807f86a0caecfbebb5f6cc8fb54`
Branch: `feature/tgps-p1-004-candidate-allocation-outcome`
Requirement: [`../requirements/TGPS-P1-004.md`](../requirements/TGPS-P1-004.md)

## Implementation and architecture

`src/tax_gps/candidate/models.py` defines frozen allocation-policy, shared-limit, deduction-treatment, allocation, outcome and result models. `engine.py` validates existing accepted input identities and readiness, constructs feasible compositions and uses `TaxState.tax_impact()` (the already accepted progressive PIT), preserving Decimal/Money semantics. `audit.py` freezes output and replays from accepted inputs. No new tax calculator, market data, ranking or recommendation layer was added. No modification to accepted P1-001/002/003 policy catalogs or their semantics.

Input direction is one-way: core/policy and existing tax/discovery/financial results feed candidate construction, then audit replays candidate output. Allocation policy is a separate explicit immutable input; the engine never silently assumes allocation equals deduction. The caller must supply accepted product/tax treatment and the true remaining common-pool capacity. The engine checks policy-to-discovery catalog identity, hashes content, and requires an explicit treatment for every allocatable item. It cannot independently attest the legal authority of arbitrary caller-supplied policy entries. A future production policy approval process must govern any new treatments; test-only synthetic multi-opportunity inputs do not activate artwork or solar in the bundled production catalog.

## Construction and outcomes

Candidate ID is SHA-256 over canonical sorted allocation JSON. NO_ACTION is first. Positive amounts come from the intersection of independent guardrail ceilings, budget, known spendable surplus, declared shared-group remainder, and the residual required to fund a subsequent opportunity at its own ceiling. Group usage is cumulative across opportunities, never independent. Empty and duplicate construction paths cannot inflate candidate count. Policy maximum is between 1 and 256; more than eight allocatable opportunities fails
before construction, and candidate-count overflow fails without returning any candidates. Non-baseline ordering is canonical allocation bytes, not economic desirability.

Every candidate records cash allocated, explicit deductible amount, progressive tax before/after/saved, cash outflow, unused budget, remaining spendable surplus, unchanged/unknown protection gap, stable reason codes, source hashes and engine version. Tax refunds are not assumed available as current cash. Existing rights remain in TaxState and do not consume new allocation budget. Partial financial state emits only the ordinary zero-allocation outcome, preserving unknown financial values. Baseline is calculated through the same tax impact path with zero deduction.

## Evidence and quality

Acceptance tests in `tests/acceptance/test_candidates.py` exercise exact employee tax outcomes (THB 79,000 before, THB 60,500 after THB 100,000 full deduction), NO_ACTION, zero budget, zero tax benefit, CAP, shared collisions, synthetic explicit partial deduction, budget residual compositions, satang boundaries, known/unknown protection, input tampering, overflow, canonical ordering, immutable policy, and replay. The full suite on the implementation tree produced 569 passed, 100.00% statement and 100.00% branch coverage. `ruff check`, `ruff format --check`, `mypy --strict`, and `uv build` passed locally. CI and exact committed SHA are pending branch publication; do not label those PASS until checked.

## Requirement coverage and deferred scope

- Candidate construction, bounds, identity, deduplication and ordering: `candidate/engine.py`, `candidate/models.py`, acceptance tests.
- Budget, per-opportunity, shared, financial and eligibility gates: `engine.py::_verify_inputs`, `_allocatable`, `build_candidates` with bounded group accounting.
- Tax, full/partial deduction and financial outcomes: `engine.py::_outcome`, existing `TaxState.tax_impact` and Money.
- Audit/replay: `candidate/audit.py`, hash/material serialization, replay tests.
- Explicit exclusions: no winner selection, optimizer, product score, return model, market service, or forward projection.

Assumption requiring reviewer attention: shared-pool remaining amount and deduction treatment arrive as independently accepted policy input. The engine checks structural consistency and declared catalog identity, but cannot prove the supplied treatment has independently approved legal provenance without an upstream governance artifact. No downstream ranking is implemented; a future separately authorized requirement must govern comparisons.

PR: pending; independent acceptance: pending; merge: not authorized.
