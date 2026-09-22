TGPS-P1-003 — Financial State & Guardrails
Implementation Report

Status: READY_FOR_INDEPENDENT_REVIEW
Requirement ID: TGPS-P1-003
Phase: 1.2 — Financial Safety Foundation
Priority: P0
Branch: feature/tgps-p1-003-financial-guardrails
Baseline commit: eaaf3410a18db2e2501a76563e3a89d4e7186c8f (384 tests, 100% coverage)


1. Implementation Summary

TGPS-P1-003 adds a fourth, independent engine layer — the Financial State & Guardrail
Engine — that sits downstream of Tax Calculation, Policy Activation, and Opportunity
Discovery. It answers a question those layers deliberately do not answer: "is spending
new cash on this opportunity financially safe right now?"

Core principle enforced throughout: tax efficiency is not financial appropriateness, and
maximum tax capacity is not a recommended allocation. The engine never ranks, scores, or
recommends. It classifies each discovered opportunity into one of five explicit decisions
(ALLOW, CAP, BLOCK, REQUIRE_REVIEW, NOT_APPLICABLE) with machine-readable reason codes and,
where relevant, a `max_feasible_allocation` Money ceiling — never a suggested amount.

Nine new modules under `src/tax_gps/financial/` (2,595 lines including tests) implement:
FinancialProfile (caller-supplied facts), FinancialGuardrailPolicy (versioned product
policy, distinct from tax law), FinancialState (deterministic derived state), the
guardrail decision matrix, the GuardrailEngine orchestrator, and GuardrailSnapshot/replay
for audit binding.


2. Architecture

Layering (unchanged separation of concerns, no monolithic orchestrator):

  Tax Engine          -> deterministic PIT calculation (TGPS-P1-001)
  Policy Engine        -> versioned rule-pack activation (TGPS-P1-001/002)
  Discovery Engine     -> opportunity/eligibility/capacity discovery (TGPS-P1-002)
  Financial State Eng. -> derives FinancialState from FinancialProfile (NEW, TGPS-P1-003)
  Guardrail Engine     -> evaluates DiscoveryResult x FinancialState -> GuardrailResult (NEW)

Each layer is a pure function of its own versioned policy/profile plus explicit inputs;
none reads a system clock or holds mutable state. The Guardrail Engine consumes, but never
mutates, DiscoveryResult and FinancialState; it adds a new independent hash chain
(`profile_hash` for financial facts, distinct from the tax-profile `profile_hash` already
carried by DiscoveryResult) so financial and tax audit trails remain separately verifiable
while both are bound into the final GuardrailResult.

Module map:

  financial/reason_codes.py  - FinancialReasonCode: 13 stable enum values (state + guardrail)
  financial/profile.py       - FinancialProfile, Debt, CommittedCashNeed, ProtectionProfile,
                                FinancialPlanningContext; all caller-supplied, no inference
  financial/policy.py        - FinancialGuardrailPolicy (PRODUCT_FINANCIAL_POLICY), readiness
                                evaluation, activation, BUNDLED_FINANCIAL_POLICY_ID_2026
  financial/state.py         - FinancialState, compute_financial_state() (deterministic)
  financial/models.py        - GuardrailDecision, GuardrailAssessment, GuardrailResult
  financial/decisions.py     - isolated DMN-style decision boundaries (one function per rule)
  financial/engine.py        - evaluate_guardrails(): precedence orchestration
  financial/audit.py         - GuardrailSnapshot, create_guardrail_snapshot(), replay_guardrails()


3. FinancialProfile Model

All facts are caller-supplied; `None` always means "unknown", never "zero" or "false".

  FinancialProfile
    liquid_assets: Money | None
    monthly_essential_expenses: Money | None
    debts: tuple[Debt, ...]                     (unique debt_id, case/whitespace-insensitive)
    committed_cash_needs: tuple[CommittedCashNeed, ...]  (unique need_id)
    protection: ProtectionProfile

  Debt
    debt_id, category (DebtCategory), outstanding_balance: Money (>=0),
    annual_percentage_rate: Decimal (>=0, exact — no float), minimum_monthly_payment: Money (>=0),
    secured: bool

  CommittedCashNeed
    need_id, amount: Money (>=0), due_date: date, mandatory: bool, description: str

  ProtectionProfile
    required_life_coverage: Money | None, existing_life_coverage: Money | None
    protection_gap: Money | None — computed ONLY when both are known, floored at zero;
    stays None (unknown) if either side is unknown — this is the canonical "unknown protection
    need is never silently zero" invariant (GR-13).

  FinancialPlanningContext
    planning_date: date (explicit; no clock read), available_budget: Money (>=0, and validated
    <= known liquid_assets — a structural consistency check owned by this layer at
    FinancialState computation time, §16 fail-closed rule).

Every structural violation raises `InvalidValueError` with a specific message (see §10 test
matrix); nothing is silently coerced.


4. FinancialState — Formulas (TGPS-P1-003 §16-21, §41)

`compute_financial_state(profile, activated_policy, context)` is a pure function: same
inputs always produce the same output, byte-for-byte, because no system clock or random
source is ever read (see §8 below for the enforcing test).

Deterministic fail-closed precondition: `liquid_assets` must be known; if `available_budget`
(caller-declared spending intent) exceeds known `liquid_assets`, computation raises
`FinancialValidationError` rather than silently proceeding.

When `monthly_essential_expenses` is unknown, the state is `PARTIAL`: every emergency-fund
figure (`emergency_reserve_floor`, `emergency_reserve_target`, `spendable_surplus`,
`emergency_fund_months`) stays `None`, and `FINANCIAL_INPUT_REQUIRED` is recorded. A PARTIAL
state can never route to ALLOW/CAP/BLOCK for new-cash opportunities — only REQUIRE_REVIEW
(GR-10).

When expenses are known (`READY`):

  emergency_reserve_floor   = monthly_essential_expenses * policy.emergency_floor_months  (3)
  emergency_reserve_target  = monthly_essential_expenses * policy.emergency_target_months (6)
  emergency_fund_months     = liquid_assets / monthly_essential_expenses  (informational only,
                               2dp string; the hard guardrail always compares Money amounts
                               directly, never the ratio, to avoid rounding-induced false ALLOWs)
  near_term_committed_cash  = sum(need.amount for mandatory needs due within
                               policy.near_term_liquidity_months of planning_date)  (12 months)
  protected_liquidity       = emergency_reserve_floor + near_term_committed_cash
  spendable_surplus         = max(0, liquid_assets - protected_liquidity)   (floored at zero,
                               never negative — §17)
  critical_debt_balance     = sum(outstanding_balance for debts with APR >= policy.critical_debt_apr)
  critical_debt_ids         = tuple of matching debt_ids (audit trail)
  protection_gap            = profile.protection.protection_gap (pass-through, unknown-safe)

All Money arithmetic uses the project's `EXACT` Decimal context (traps Inexact/Rounded — no
binary float, no silent rounding). `state_hash` = sha256(canonical_json(material_dict())),
binding policy_id/version/hash, profile_hash, planning_date, and every derived figure.


5. Policy / Version / Provenance

`FinancialGuardrailPolicy` is a versioned, activatable object mirroring the pattern already
used for Tax Rule Packs (TGPS-P1-001) and the Opportunity Catalog (TGPS-P1-002):

  policy_id, version, status (DRAFT/UNAPPROVED/EFFECTIVE/EXPIRED/INVALID),
  effective_from, effective_to, basis_sources, review_notes, content_hash()

Bundled policy: `TH-FIN-GUARDRAIL-2026-001`, version `1.0.0`, status EFFECTIVE, effective
2026-01-01..2026-12-31.

`activate_financial_policy()` calls `evaluate_financial_policy_readiness()` and raises
`FinancialPolicyActivationError(findings)` if the policy is not ready — the guardrail
engine can never run against a structurally invalid or non-EFFECTIVE policy. This mirrors
TGPS-P1-002's fail-closed readiness pattern exactly (same shape, own module).


6. PRODUCT POLICY — NOT LAW (governance boundary, explicit)

The following four parameters in `bundled_financial_policy()` are Tax GPS PRODUCT FINANCIAL
POLICY. They are internal product safety defaults, not Thai statute, not Bank of Thailand
regulation, and not tax law:

  emergency_floor_months  = 3   (general personal-finance planning guidance, not statutory)
  emergency_target_months = 6   (general personal-finance planning guidance, not statutory)
  critical_debt_apr       = 15% (Tax GPS's own conservative safety threshold; Thai credit-card
                                  APR can reach ~16% p.a., so 15% is chosen as an internal
                                  trigger below the typical market ceiling — NOT a BoT-mandated
                                  rate cap or disclosure threshold)
  near_term_liquidity_months = 12  (Tax GPS product default for "near-term" committed-cash
                                     horizon; not a statutory notice period)

This distinction is encoded in code, not only in this report: `POLICY_CLASSIFICATION =
"PRODUCT_FINANCIAL_POLICY"` is embedded in every `FinancialGuardrailPolicy.to_dict()` output
and `review_notes`, and `basis_sources` on the bundled policy explicitly states "not Thai
statute" / "not a Bank of Thailand ... threshold" for each parameter. Any future change to
these thresholds is a product decision requiring its own review — it must never be
represented to the user, in code comments, or in outputs as a legal/tax requirement.


7. Guardrail Precedence (TGPS-P1-003 §43, mirrored 1:1 in financial/engine.py's module
   docstring and evaluate_guardrails()/assess_new_cash_opportunity() code path)

  1. Upstream discovery availability   -> discovery.status != READY: everything NOT_APPLICABLE
                                           per-opportunity: RULE_NOT_READY / REQUIRES_INPUT /
                                           INELIGIBLE / OUTSIDE_EFFECTIVE_PERIOD -> NOT_APPLICABLE
                                           (guardrails never promote an upstream-unavailable
                                           opportunity to ALLOW/CAP)
  2. Financial policy readiness        -> enforced before evaluate_guardrails() can even be
                                           called (activate_financial_policy fails closed)
  3. Required financial input completeness -> FinancialState.status == PARTIAL ->
                                           REQUIRE_REVIEW (FINANCIAL_INPUT_REQUIRED); never ALLOW
  4. Critical high-cost debt           -> critical_debt_balance > 0:
                                             intrinsic-purpose opportunity -> REQUIRE_REVIEW
                                             otherwise (INVESTMENT_TAX etc.)  -> BLOCK
  5. Emergency-fund floor              -> liquid_assets < emergency_reserve_floor:
                                             intrinsic-purpose opportunity -> REQUIRE_REVIEW
                                             otherwise                        -> BLOCK
  6. Mandatory liquidity commitments   -> folded into protected_liquidity, which lowers
                                           spendable_surplus (step 7) rather than being a
                                           separate branch
  7. Allocation ceiling / CAP          -> spendable_surplus == 0: intrinsic -> REQUIRE_REVIEW,
                                           else BLOCK; spendable_surplus < ceiling -> CAP
                                           (max_feasible_allocation = spendable_surplus);
                                           else -> ALLOW (max_feasible_allocation = min(ceiling,
                                           surplus))
  8. Protection informational warning  -> appended to reason_codes only, never changes decision
                                           (PROTECTION_GAP or PROTECTION_NEED_UNKNOWN)
  9. Existing rights                   -> bypass steps 1-8 entirely: always ALLOW,
                                           max_feasible_allocation = None
                                           (EXISTING_RIGHT_PASSTHROUGH) — an existing legal
                                           entitlement is never financially gated.

Steps 4 and 5 are each independently checked via `critical_debt_decision()` /
`emergency_floor_decision()`, short-circuiting with `or` — critical debt takes precedence
over the emergency-fund check when both apply (matches §32-35 ordering).


8. Guardrail Decision Matrix (verified against implementation)

  Discovery status != READY                                -> NOT_APPLICABLE  (never promoted)
  Existing right (tax_status kind = existing right)          -> ALLOW (pass-through, no ceiling)
  FinancialState.status == PARTIAL (expenses unknown)         -> REQUIRE_REVIEW
  Critical debt present + intrinsic-purpose opportunity       -> REQUIRE_REVIEW
  Critical debt present + non-intrinsic (e.g. INVESTMENT_TAX) -> BLOCK, ceiling = 0
  Liquid assets < emergency floor + intrinsic-purpose          -> REQUIRE_REVIEW
  Liquid assets < emergency floor + non-intrinsic (INVESTMENT_TAX) -> BLOCK, ceiling = 0
  spendable_surplus == 0 + intrinsic-purpose                  -> REQUIRE_REVIEW
  spendable_surplus == 0 + non-intrinsic                       -> BLOCK, ceiling = 0
  0 < spendable_surplus < remaining_capacity/budget ceiling    -> CAP, ceiling = spendable_surplus
  spendable_surplus >= ceiling (healthy)                        -> ALLOW, ceiling = min(ceiling, surplus)
  Protection gap known and positive                            -> informational reason code only
  Protection need unknown (required_life_coverage is None)     -> informational reason code only,
                                                                    never coerced to "no gap"

"Intrinsic-purpose" opportunities are `UTILITY_INVESTMENT` and `LIFESTYLE_INTENT`
(`is_intrinsic_purpose()`), i.e. opportunities whose value is not purely tax-motivated new
cash deployment — REQUIRE_REVIEW rather than an automatic BLOCK respects that the user may
have a standing non-tax reason to proceed even under financial stress, while still refusing
to silently ALLOW.

`max_feasible_allocation` is documented in `financial/models.py`'s module docstring as "a
safety ceiling, not advice" and is never populated with a recommended amount — it is either
`None` (no ceiling applies / not computed), `Money.zero()` (BLOCK), or
`min(remaining_capacity, available_budget, spendable_surplus)` (CAP/ALLOW ceiling).


9. Reason Codes

13 stable `FinancialReasonCode` enum values (financial/reason_codes.py), each independently
unit-tested for the exact code it produces (never merely "an exception was raised"):

  EXISTING_RIGHT_PASSTHROUGH, FINANCIAL_INPUT_REQUIRED,
  EMERGENCY_FUND_BELOW_FLOOR, EMERGENCY_FUND_PRESERVED, ZERO_ESSENTIAL_EXPENSE_BASE,
  CRITICAL_DEBT_PRESENT,
  LIQUIDITY_COMMITMENT_CONFLICT, ALLOCATION_CAPPED_BY_LIQUIDITY, NO_SPENDABLE_SURPLUS,
  PROTECTION_GAP, PROTECTION_NEED_UNKNOWN,
  UPSTREAM_NOT_AVAILABLE, GUARDRAIL_POLICY_NOT_READY


10. Determinism

`compute_financial_state()` and `evaluate_guardrails()` take every time-varying input
explicitly (`FinancialPlanningContext.planning_date`); neither imports `datetime.date.today()`
or any other clock/random source. `test_fin_01_deterministic_no_clock_reads` asserts this by
computing state twice with an identical (frozen) planning_date and comparing hashes, and by
static source inspection that no clock-reading calls exist in state.py.

Verified determinism dimensions (each independently re-computed and hash-compared):
  - FinancialState / FinancialState.state_hash: identical inputs -> identical hash;
    any single material field change -> different hash
  - GuardrailResult / GuardrailResult.guardrail_hash: same guarantee, transitively bound to
    FinancialState.state_hash, ActivatedFinancialPolicy.content_hash, and
    DiscoveryResult.discovery_hash/profile_hash


11. Audit / Replay

`GuardrailSnapshot` freezes every input hash plus the full canonical `guardrail_output` JSON
and `guardrail_hash`. `create_guardrail_snapshot()` rejects an unhashed or mismatched result
before persisting (fail closed at snapshot time, not only at replay time).
`replay_guardrails()` recomputes guardrails fresh from the snapshot's declared inputs and
independently verifies EVERY material replay dimension named in this requirement, each with
its own `GuardrailReplayError` and a distinct assertion in tests/unit/financial/test_audit.py:

  profile hash mismatch              -> GuardrailReplayError("profile does not match ...")
  discovery result hash mismatch     -> GuardrailReplayError("discovery result does not match ...")
  financial state hash mismatch      -> GuardrailReplayError("financial state does not match ...")
  financial policy id/version/hash mismatch -> GuardrailReplayError("financial policy does not match ...")
  planning date mismatch             -> GuardrailReplayError("planning context does not match ...")
  available budget mismatch          -> GuardrailReplayError("planning context does not match ...")
  engine version mismatch            -> GuardrailReplayError("engine version does not match ...")
  guardrail output/hash mismatch (forged snapshot) -> GuardrailReplayError("guardrail output
                                          hash does not match replay" / "... output does not
                                          match replay") — belt-and-braces: hash AND full
                                          output are both compared, so a hash collision alone
                                          cannot pass replay.

Snapshot creation-time consistency (a snapshot cannot even be built from mismatched inputs)
is separately tested: profile_hash, discovery_hash, financial_state_hash,
financial_policy_hash, planning_date, and available_budget mismatches each raise `ValueError`
at `create_guardrail_snapshot()`.


12. Independent Adversarial Review (fresh-context, read-only)

A fresh-context subagent (claude-opus-4-8) independently reviewed the implementation against
the spec across 10 dimensions: financial safety correctness, guardrail precedence,
unknown-vs-zero semantics, upstream-status preservation, available-budget/liquidity math,
critical-debt threshold boundaries, audit/replay completeness, no-recommendation-leakage,
test independence, and scope creep. It verified claims against source directly rather than
trusting this report's draft. Verdicts: 8x PASS, 2x PASS-with-CONCERN. Overall verdict:
READY for independent project acceptance review, no blocking bugs, three non-blocking
findings — all three were then FIXED before close-out:

  1. Fail-open denylist in engine._assess_new_cash: the original implementation matched
     opportunity status against a hard-coded set of four "unavailable" statuses and treated
     everything else as AVAILABLE by default — safe today only because that set happened to
     be exhaustive against the current OpportunityStatus enum, but a future enum addition
     would have silently been promoted into the new-cash guardrail path. FIXED: inverted to
     a fail-closed allowlist (`if item.status is not OpportunityStatus.AVAILABLE:
     NOT_APPLICABLE`) — any status other than the explicit AVAILABLE value, present or
     future, is refused by default. See financial/engine.py `_assess_new_cash`.

  2. Missing critical-debt APR equality-boundary test: the `>=` comparison
     (state.py `_critical_debt`) was correct against §27 but had no test pinning the exact
     0.15 boundary or a just-below value. FIXED: added
     `test_debt_at_exactly_the_critical_apr_threshold_is_classified_critical` (APR = 0.15,
     must classify critical) and
     `test_debt_just_below_the_critical_apr_threshold_is_not_classified_critical`
     (APR = 0.1499, must not classify critical) to tests/unit/financial/test_state.py,
     both marked `@pytest.mark.boundary`.

  3. Existing-rights-under-UNSUPPORTED-discovery behavior was intentional (§30 — existing
     rights bypass the availability gate entirely) but untested. FIXED: added
     `test_existing_right_still_allows_even_when_discovery_is_unsupported` to
     tests/unit/financial/test_engine.py, which constructs an UNSUPPORTED DiscoveryResult
     carrying a real existing right (via `dataclasses.replace` on an otherwise-READY
     fixture) and asserts the right still resolves ALLOW while every new-cash opportunity in
     the same result resolves NOT_APPLICABLE. The test's docstring records that production
     discovery never actually emits existing_rights under UNSUPPORTED (verified against
     discovery/engine.py's UNSUPPORTED branch, which always sets `existing_rights=()`), so
     this exercises the guardrail engine's own contract in isolation, independent of that
     upstream guarantee.

All three fixes are reflected in the final test/coverage counts in §12 (509 tests, up from
the review's as-reviewed 504) and §13 below.


13. Tests

New test files (all under tests/unit/financial/ and tests/acceptance/):

  tests/acceptance/test_guardrails.py   368 lines  GR-01..16 + G05-G07 (mandatory/golden markers)
  tests/unit/financial/test_state.py    225 lines  FIN-01..05 + branch-closing cases
  tests/unit/financial/test_decisions.py 165 lines  isolated decision-boundary unit tests
  tests/unit/financial/test_engine.py    97 lines  precedence/validation edge cases
  tests/unit/financial/test_audit.py    202 lines  19 replay/snapshot rejection tests
  tests/unit/financial/test_policy.py   160 lines  21 policy readiness/activation tests
  tests/unit/financial/test_profile.py  235 lines  31 structural validation tests

Plus 3 new Money.times() tests (mutation/quantization) in tests/unit/core/test_money.py.

Total suite: 509 tests collected, 509 passed, 0 failed (baseline was 384; net +125).

Marker suite counts (all pass):
  mandatory: 73 passed
  golden:    11 passed
  negative: 160 passed
  replay:    19 passed
  boundary:  11 passed


14. Coverage

  uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing
  TOTAL: 2372 statements, 0 missed, 624 branches, 0 partial -> 100.00% statement, 100.00% branch
  Required test coverage of 100.0% reached.

This is whole-package (`tax_gps`) coverage, not module-scoped.

Retained coverage exclusions (5 total, all in new TGPS-P1-003 code; each reviewed and
justified as genuinely unreachable by construction — no malformed external/runtime input can
reach them):

  1. financial/decisions.py:86-88 (emergency_floor_decision)
     `state.liquid_assets is None or state.emergency_reserve_floor is None`
     Unreachable because `assess_new_cash_opportunity()` (the sole caller) routes any
     FinancialState with status PARTIAL to `financial_input_required()` before this function
     is ever invoked (financial/decisions.py:160-161), and `compute_financial_state()`
     guarantees liquid_assets and emergency_reserve_floor are set together (both None only in
     the PARTIAL branch, both Money otherwise) — see state.py:184-224. Defensive-only.

  2. financial/decisions.py:110 (liquidity_ceiling_decision)
     `if surplus is None`
     Same guarantee as #1: `spendable_surplus` is only None when FinancialState is PARTIAL,
     and PARTIAL states never reach `liquidity_ceiling_decision()` (short-circuited earlier in
     `assess_new_cash_opportunity()`). Defensive-only.

  3. financial/engine.py:62 (`_assess_new_cash`)
     `if remaining_capacity is None`
     Verified by inspection of `discovery/engine.py`: every code path that constructs a
     `DiscoveredOpportunity` with `status=OpportunityStatus.AVAILABLE` always supplies
     `remaining_capacity=capacity.remaining_capacity` (a concrete `Money`, engine.py:297-304);
     `remaining_capacity=None` is used exclusively by the seven non-AVAILABLE status branches
     (engine.py:203-268), all of which are filtered out by the guardrail engine's
     `_UPSTREAM_UNAVAILABLE_STATUSES` check one line earlier. No AVAILABLE opportunity can
     ever carry a None capacity.

  4. financial/profile.py:42 (`canonical_apr`)
     `if not isinstance(exponent, int)`
     `Decimal.as_tuple().exponent` is only non-int (`"n"`/`"N"`/`"F"`) for NaN/Infinity
     decimals. `canonical_apr()` is only ever called on a `Decimal` that has already passed
     `parse_decimal()` (core/decimal_context.py:33-49), which explicitly rejects
     non-finite Decimals (`if not value.is_finite(): raise error(...)`) before any `Decimal`
     reaches this function. A non-finite APR cannot reach `canonical_apr`.

  5. financial/state.py:120 (`_emergency_fund_months`)
     `except DecimalException`
     Both operands are `Money.amount` values, and `Money.__post_init__` (core/money.py:30-31)
     rejects any non-finite Decimal at construction time; division/quantization of two finite,
     bounded-precision Decimals under the project's 50-digit `_ROUNDING_CONTEXT` cannot signal
     Inexact/Rounded/Overflow given the values Money can hold. Defensive-only, matching the
     identical pattern already accepted in `core/decimal_context.py:74` and
     `core/canonical.py` from the TGPS-P1-001/002 baseline.

All five mirror an existing, already-accepted pattern in the pre-TGPS-P1-003 codebase
(`core/decimal_context.py:74`, `raise AssertionError("unreachable"` project-wide exclusion in
`pyproject.toml`'s `[tool.coverage.report] exclude_also`), so no new exclusion category was
introduced.


15. CI

  uv run ruff check .                → All checks passed! (89 files)
  uv run ruff format --check .       → 89 files already formatted
  uv run mypy --strict               → Success: no issues found in 84 source files
  uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing
                                       → 504 passed, 100.00% statement + branch coverage
  uv build                            → Successfully built dist/tax_gps_core-0.1.1.tar.gz
                                         and dist/tax_gps_core-0.1.1-py3-none-any.whl

GitHub Actions CI run: see git/CI close-out section below (populated after push/PR).


16. Requirement Mapping (TGPS-P1-003 section -> implementation)

  §8-15   FinancialProfile model, structural validation        -> financial/profile.py
  §16-21  FinancialState derivation formulas                    -> financial/state.py
  §22, 26 Fail-closed on unknown/invalid inputs                 -> state.py, profile.py raises
  §23-26  Versioned product financial policy, activation        -> financial/policy.py
  §28     GuardrailDecision enum (no PENALIZE/scoring)          -> financial/models.py
  §30     Existing rights never financially blocked             -> decisions.existing_right_passthrough
  §32-35  Critical debt / emergency floor precedence            -> decisions.py, engine.py
  §36-38  Liquidity ceiling (CAP/ALLOW/BLOCK by surplus)        -> decisions.liquidity_ceiling_decision
  §39-40  Protection informational-only warning                 -> decisions.with_protection_reason
  §41     PARTIAL state -> REQUIRE_REVIEW, never ALLOW           -> decisions.financial_input_required
  §43     Full precedence order                                  -> engine.py module docstring + code
  §44, 47 No recommendation/scoring leakage                      -> models.py docstring + matrix
  §45-48  GuardrailResult shape, Discovery-order preservation    -> financial/models.py, engine.py
  §52-53  GuardrailSnapshot + deterministic replay                -> financial/audit.py
  §66-74  Acceptance criteria / test matrix                       -> tests/acceptance/test_guardrails.py
                                                                     (GR-01..16, G05-G07)


17. Deviations

None from the written requirement. The one design choice made where the spec left an
implementation detail open: `Money.times(factor: int) -> Money` was added to the core
primitive layer (see §17 below) rather than duplicating month-count multiplication logic
inside the financial module.


18. Assumptions

  - "Intrinsic-purpose" opportunity categories are fixed to `UTILITY_INVESTMENT` and
    `LIFESTYLE_INTENT` per the existing `OpportunityCategory` enum from TGPS-P1-002; no new
    categories were introduced.
  - `available_budget` consistency (must not exceed known `liquid_assets`) is treated as a
    FinancialState-layer concern (raised inside `compute_financial_state`) rather than a
    separate Guardrail-layer precondition, since it is a property of the caller-declared
    planning context, not of any individual opportunity.
  - The bundled policy's `effective_to` is scoped to the calendar year matching the supplied
    `TaxYear`, mirroring the existing Rule Pack / Opportunity Catalog activation pattern.


19. Open Issues

  - None blocking. The Guardrail Engine is not yet wired into any orchestrating endpoint or
    CLI (out of scope per TGPS-P1-003; API/orchestration is explicitly deferred to a later
    phase per the requirement's stated exclusions).
  - TGPS-P1-004 (Candidate Allocation & Outcome Engine) remains blocked pending this PR's
    merge, per instruction — not started.


20. BPMN / DMN Impact

The guardrail decision functions in `financial/decisions.py` are structured 1:1 as DMN
decision-table rules (one function = one rule, explicit inputs/outputs, no fallthrough
branching inside a function) specifically so a future BPMN/DMN modeling exercise can
transcribe them without re-deriving logic from prose. `evaluate_guardrails()` documents the
9-step precedence order in its module docstring in the same order a DMN decision table's
hit-policy rows would be authored (first-match, top-down), enabling direct BPMN swimlane
mapping: Discovery Engine -> Financial State Engine -> Guardrail Engine as three sequential
service tasks with the precedence chain as the Guardrail Engine's internal business rule
task.


21. Git State

  Branch:              feature/tgps-p1-003-financial-guardrails
  Baseline commit:      eaaf3410a18db2e2501a76563e3a89d4e7186c8f
  Working tree (pre-commit): modified src/tax_gps/core/money.py, tests/unit/core/test_money.py;
                              untracked src/tax_gps/financial/, tests/unit/financial/,
                              tests/acceptance/test_guardrails.py, docs/requirements/TGPS-P1-003.md,
                              this report

  (Implementation commit hash, PR URL, and CI run URL/conclusion are recorded in the final
  close-out message returned to the requester after commit/push/PR — not duplicated here to
  avoid this file going stale relative to the actual git history.)
