TGPS-P1-003-R1 — Independent Acceptance Remediation
Close-out Report

Status: REMEDIATION COMPLETE, READY FOR RE-REVIEW
Parent: TGPS-P1-003 — Financial State & Guardrails
PR: #2 (unmerged, remediation commit(s) added on top)
Reviewed commit (unmodified): 264e84a5b7c83da579a993c1dc9cfc16a10cbdab
Branch: feature/tgps-p1-003-financial-guardrails


1. Scope

Three acceptance gaps (R1-01, R1-02, R1-03) were identified against the reviewed commit and
are closed here. Two additional fail-closed gaps found during remediation (R1-04, R1-05) are
also closed and documented, since they share the same root cause class (implicit
None-as-zero / unreachable-by-assumption fallbacks) as R1-01/R1-02.

The reviewed implementation commit `264e84a5` was NOT amended. All remediation is in
working-tree changes on top of it, to be captured in a separate remediation commit.


2. R1-01 — Unknown Liquid Assets as Partial Financial Data

Before: `liquid_assets = None` raised `FinancialValidationError` in
`compute_financial_state()` before any `FinancialState` could exist, blocking every
guardrail evaluation (including existing rights, which never require liquidity).

After (src/tax_gps/financial/state.py, `compute_financial_state`):
  - `available_budget <= liquid_assets` is only evaluated when `liquid_assets` is known
    (narrowed under an explicit `if liquid_assets_known:` guard).
  - `FinancialState.status = PARTIAL` whenever EITHER `liquid_assets` OR
    `monthly_essential_expenses` is unknown (previously only expenses were checked).
  - All liquidity-derived fields (`emergency_fund_months`, `emergency_reserve_floor`,
    `emergency_reserve_target`, `protected_liquidity`, `spendable_surplus`) remain `None`
    unless BOTH liquid_assets and expenses are known.
  - `FinancialReasonCode.FINANCIAL_INPUT_REQUIRED` is recorded whenever either is unknown.
  - Unknown liquid assets is never coerced to `Money.zero()` anywhere in the derivation path.

Guardrail routing (src/tax_gps/financial/decisions.py, `assess_new_cash_opportunity`,
unchanged logic, now exercised by the new PARTIAL path):
  - `FinancialState.status is PARTIAL` -> `financial_input_required()` -> REQUIRE_REVIEW /
    FINANCIAL_INPUT_REQUIRED for every new-cash opportunity, unconditionally.
  - `existing_right_passthrough()` is called directly by the guardrail engine for every
    existing right, bypassing FinancialState entirely -> ALLOW regardless of liquidity
    knowledge.

Mandatory tests added:
  - tests/acceptance/test_guardrails.py::test_gr_17_unknown_liquid_assets_existing_right_still_allows
    (unknown liquid assets + existing right -> ALLOW / EXISTING_RIGHT_PASSTHROUGH)
  - tests/acceptance/test_guardrails.py::test_gr_18_unknown_liquid_assets_new_cash_requires_review
    (unknown liquid assets + AVAILABLE Thai ESG -> REQUIRE_REVIEW / FINANCIAL_INPUT_REQUIRED,
    result.status == PARTIAL)
  - tests/unit/financial/test_state.py::test_budget_without_known_liquid_assets_is_not_evaluated_against_liquid_assets
  - tests/unit/financial/test_state.py::test_unknown_liquid_assets_leave_liquidity_derived_fields_unknown

Superseded test: the old `test_budget_without_known_liquid_assets_fails_closed` (asserted
FinancialValidationError on `liquid_assets=None`) was replaced — that behavior is exactly
what R1-01 requires NOT to happen. The still-required fail-closed behavior (available_budget
exceeding a KNOWN liquid_assets) remains covered by GR-11
(`test_gr_11_budget_greater_than_liquid_assets_fails_closed`), unchanged.


3. R1-02 — FinancialState Self-Integrity at Snapshot / Replay Boundaries

New: `verify_financial_state_integrity(state)` (src/tax_gps/financial/state.py) recomputes
`sha256_hex(canonical_json(state.material_dict()))` from the state's own current field values
and raises `FinancialStateIntegrityError` (a new `InvalidValueError` subclass) on any
mismatch against the carried `state.state_hash`. This does not trust `state_hash` at face
value at either boundary; the equality it enforces is `state_hash == hash(material_dict())`,
not merely `state_hash == some other snapshot's copy of state_hash`.

Wired into BOTH required trust boundaries in src/tax_gps/financial/audit.py:
  - `create_guardrail_snapshot()`: calls `verify_financial_state_integrity(state)` before
    checking result-vs-inputs consistency; failure raises `ValueError` with a
    "failed self-integrity verification" message.
  - `replay_guardrails()`: calls `verify_financial_state_integrity(state)` before comparing
    `snapshot.financial_state_hash` against `state.state_hash`; failure raises
    `GuardrailReplayError` with the same message pattern.

Required tests added (tests/unit/financial/test_state.py, `@pytest.mark.replay`):
  1. `test_verify_financial_state_integrity_rejects_mutated_liquid_assets_with_stale_hash`
  2. `test_verify_financial_state_integrity_rejects_mutated_critical_debt_with_stale_hash`
  3. `test_verify_financial_state_integrity_rejects_mutated_reason_codes_with_stale_hash`
     (protection/commitment-derived reason-code data mutated, hash stale)
  4. `test_verify_financial_state_integrity_rejects_mutated_protection_gap_with_stale_hash`
     — the mandated "decision would otherwise remain identical" case: `protection_gap` is
     purely informational (§39-40) and never changes BLOCK/CAP/ALLOW, so a GuardrailResult
     diff alone would never catch this tampering; only direct FinancialState hash
     verification does.
  Plus a positive control: `test_verify_financial_state_integrity_accepts_untampered_state`.

Boundary-level tests added (tests/unit/financial/test_audit.py):
  - `test_create_snapshot_rejects_tampered_financial_state_with_stale_hash`
  - `test_replay_rejects_tampered_financial_state_with_stale_hash`
  Both construct a `state` via `compute_financial_state()`, then `dataclasses.replace()` a
  material field (`liquid_assets`) while leaving `state_hash` untouched, and assert the
  specific boundary function fails closed with the self-integrity message.


4. R1-03 — Policy Effective-Date and Provenance Readiness

4a. Effective-period enforcement against planning_date

New: `evaluate_financial_policy_temporal_readiness(policy, planning_date)`
(src/tax_gps/financial/policy.py) returns non-empty findings
(`PLANNING_DATE_BEFORE_POLICY_EFFECTIVE_FROM` / `PLANNING_DATE_AFTER_POLICY_EFFECTIVE_TO`)
when `planning_date` falls outside `[effective_from, effective_to]`. This is distinct from
`evaluate_financial_policy_readiness()` (structural/status readiness, independent of any
planning date) so a policy's structural validity and its applicability to a specific
planning date remain separately testable.

`compute_financial_state()` now calls this check first and raises `FinancialValidationError`
("financial policy is not effective for the planning date (fail closed)") if it fails —
before any FinancialState is derived. An EFFECTIVE-status policy whose `effective_to` has
passed relative to `planning_date` can no longer be silently applied; the example in the
remediation brief (`effective_to=2026-12-31`, `planning_date=2027-01-01`) now fails closed.

Existing structural check `effective_from <= effective_to` was already enforced in
`_validate_structure()` (`INVALID_EFFECTIVE_PERIOD`) and remains unchanged/covered.

4b. Structured provenance, not arbitrary text

`basis_sources: tuple[str, ...]` (bare strings, verified only non-empty) was replaced with
`basis_sources: tuple[FinancialPolicySource, ...]`, a structured dataclass:

  FinancialPolicySource
    source_id: str, publisher: str, title: str, url: str,
    authority: FinancialPolicySourceAuthority (CENTRAL_BANK_REGULATOR |
               MARKET_EDUCATION_BODY)

`_has_valid_source_metadata()` requires non-blank `source_id`/`publisher`/`title` and an
HTTPS URL with a resolvable hostname (mirrors the existing HTTPS/authority gate pattern
already used in `tax_gps.policy.readiness`). `_validate_structure()` now emits
`INVALID_BASIS_SOURCE_METADATA:<source_id>` per invalid source instead of only checking
tuple non-emptiness, closing "invalid source metadata -> policy not ready" (canonical
requirement).

The bundled policy's two `basis_sources` entries are now genuine external citations:
  - SET (Stock Exchange of Thailand, SET Investnow investor-education): emergency fund
    guidance of approximately 3-6 months of expenses (backs `emergency_floor_months=3`,
    `emergency_target_months=6`)
  - Bank of Thailand: the ~16% p.a. credit-card interest/fee ceiling notification (backs,
    but is explicitly NOT equal to, `critical_debt_apr=0.15`)

`review_notes` explicitly states the 15% `critical_debt_apr` threshold is a Tax GPS PRODUCT
FINANCIAL POLICY decision informed by, but distinct from, the Bank of Thailand's ~16% p.a.
ceiling, and is NOT a Bank of Thailand regulatory threshold — preserving the governance
boundary from the original implementation report §6.

4c. Year-scoped policy identity (defensive, closes a related silent-mismatch risk)

`bundled_financial_policy(tax_year)` now rejects any `tax_year != TaxYear(2026)` with
`FinancialPolicyValidationError`, rather than silently constructing a policy whose
`effective_from`/`effective_to` shift to a different calendar year while its `policy_id`
(`TH-FIN-GUARDRAIL-2026-001`) still claims 2026. All existing callers already pass
`TaxYear(2026)` exclusively (verified by repo-wide search), so this is non-breaking.

Tests added/updated (tests/unit/financial/test_policy.py — file rewritten):
  - `test_planning_date_within_effective_period_has_no_temporal_findings`
  - `test_planning_date_after_effective_to_fails_closed` (the canonical example, `@negative`)
  - `test_planning_date_before_effective_from_fails_closed` (`@negative`)
  - `test_planning_date_exactly_on_effective_to_is_within_period` (`@boundary`)
  - `test_planning_date_exactly_on_effective_from_is_within_period` (`@boundary`)
  - `test_temporal_readiness_with_no_effective_to_never_expires`
  - `test_non_https_basis_source_url_is_a_readiness_finding` (`@negative`)
  - `test_blank_basis_source_fields_are_a_readiness_finding` (`@negative`)
  - `test_valid_structured_basis_source_is_accepted`
  - `test_bundled_policy_rejects_non_2026_tax_year` / `..._a_year_before_2026` (`@negative`)
  - full re-assertion of every prior structural-finding test against the new
    `FinancialPolicySource`-based fixtures (target below the floor, negative APR, missing
    id/version, non-EFFECTIVE status, etc. — all retained)

Acceptance-level test added (tests/acceptance/test_guardrails.py):
  - `test_gr_19_out_of_period_policy_fails_closed` — reproduces the canonical example against
    `compute_financial_state()` end-to-end.


5. Additional fail-closed gaps found and closed during remediation

These were not in the original three items but were uncovered while implementing R1-01/02
and share the same "implicit None/absence treated as safe" root cause; both are minimal,
targeted, and covered by new mandatory/negative tests.

R1-04 — AVAILABLE opportunity with unknown remaining_capacity silently used available_budget
as its ceiling (`src/tax_gps/financial/engine.py`, previously marked
`# pragma: no cover - AVAILABLE always carries capacity`). This assumed invariant is not
structurally enforced by `DiscoveredOpportunity` (`remaining_capacity: Money | None` is legal
on an AVAILABLE item). Fixed: a new `missing_capacity()` decision
(`FinancialReasonCode.DISCOVERY_CAPACITY_MISSING`, new reason code) returns NOT_APPLICABLE
instead of falling back to `available_budget`. Covered by
`test_gr_20_available_opportunity_with_unknown_capacity_fails_closed`.

R1-05 — `_emergency_fund_months`'s `except DecimalException` branch
(`src/tax_gps/financial/state.py`) was marked unreachable by the original implementation
report (§14 item 5), but is in fact reachable: `Money` permits significant-digit counts
(observed up to ~47 digits before the 50-digit `_ROUNDING_CONTEXT` precision is exceeded by
the ratio) that exceed the ratio's representable precision for extreme liquid_assets /
tiny-expense combinations. Verified by direct probe
(`Money.of("9"*47 + ".00")` / `Money.of("0.01")` raises `decimal.InvalidOperation` inside
`_ROUNDING_CONTEXT.divide`). Pragma removed; covered by
`test_emergency_fund_months_raises_when_ratio_exceeds_context_precision`.

Two further genuinely-defensive `# pragma: no cover` removals in
`src/tax_gps/financial/decisions.py` (`emergency_floor_decision`'s liquid_assets/
emergency_reserve_floor None-guard, `liquidity_ceiling_decision`'s surplus None-guard) — both
functions are exported and independently callable outside
`assess_new_cash_opportunity()`'s PARTIAL-routing guarantee, so they now fail closed rather
than relying on an invariant enforced only by their sole current caller. Covered directly by
three new tests in tests/unit/financial/test_decisions.py (not merely re-exercised via the
orchestrator).


6. Quality Gates (final, post-remediation)

  uv run ruff check .                                    -> All checks passed! (90 files)
  uv run ruff format --check .                            -> 90 files already formatted
  uv run mypy --strict src tests                           -> Success: no issues found in
                                                                84 source files
  uv run pytest --cov=tax_gps --cov-branch
      --cov-report=term-missing                            -> 538 passed, 100.00% statement,
                                                                100.00% branch coverage
                                                                (TOTAL 2435 stmts / 0 missed,
                                                                648 branches / 0 partial)
  uv build                                                  -> Successfully built
                                                                dist/tax_gps_core-0.1.1.tar.gz
                                                                and
                                                                dist/tax_gps_core-0.1.1-py3-none-any.whl

All 5 pragma: no cover exclusions from the original TGPS-P1-003 report were re-reviewed:
  #1 (emergency_floor_decision None-guard) — pragma removed, now covered directly.
  #2 (liquidity_ceiling_decision surplus None-guard) — pragma removed, now covered directly.
  #3 (engine._assess_new_cash remaining_capacity is None) — pragma removed; this was R1-04,
      now a real fail-closed branch, covered.
  #4 (profile.canonical_apr non-int exponent) — re-verified still genuinely unreachable
      (Money construction rejects non-finite Decimals before this function can be reached);
      retained as-is, unchanged.
  #5 (state._emergency_fund_months DecimalException) — pragma removed; this was R1-05, now a
      real reachable branch, covered.

Net: 1 of 5 original exclusions retained (profile.py:42, re-verified genuinely unreachable);
4 were found to be either newly-fixed fail-closed gaps (R1-04, R1-05) or defensive branches
now independently tested rather than assumed-unreachable (decisions.py x2).


7. Test Suite Growth and Marker Counts

Baseline (as independently reviewed): 509 passed, 100% coverage.
Post-remediation: 538 passed, 100% statement + branch coverage (net +29 tests).

Marker suite counts (pytest --collect-only -q -m <marker>):
  mandatory: 77 collected
  boundary:  13 collected
  golden:    11 collected
  negative: 176 collected
  replay:    24 collected

(Markers are not mutually exclusive; a test may carry more than one, e.g.
`@pytest.mark.mandatory @pytest.mark.negative`.)


8. Files Changed (working tree, on top of unmodified 264e84a5)

  src/tax_gps/financial/state.py       — R1-01 (PARTIAL on unknown liquid_assets), R1-02
                                          (verify_financial_state_integrity,
                                          FinancialStateIntegrityError), R1-03a (temporal
                                          readiness check wired into compute_financial_state),
                                          R1-05 (pragma removed)
  src/tax_gps/financial/policy.py      — R1-03 (FinancialPolicySource, structured provenance,
                                          evaluate_financial_policy_temporal_readiness,
                                          year-scoped bundled policy identity) — file rewritten
  src/tax_gps/financial/audit.py       — R1-02 (integrity check wired into
                                          create_guardrail_snapshot and replay_guardrails)
  src/tax_gps/financial/engine.py      — R1-04 (missing_capacity fail-closed branch)
  src/tax_gps/financial/decisions.py   — R1-04 (missing_capacity()), defensive-branch pragma
                                          removals with direct tests
  src/tax_gps/financial/reason_codes.py — new DISCOVERY_CAPACITY_MISSING reason code

  tests/unit/financial/test_state.py    — R1-01, R1-02, R1-05 tests; superseded test updated
  tests/unit/financial/test_policy.py   — rewritten for R1-03 (structured sources, temporal
                                           readiness, year-scoping)
  tests/unit/financial/test_audit.py    — R1-02 boundary tests
  tests/unit/financial/test_decisions.py — defensive-branch direct tests
  tests/acceptance/test_guardrails.py    — GR-17..20 (R1-01, R1-03, R1-04 acceptance tests);
                                           `_financial_profile` helper widened to accept
                                           `liquid_assets: int | None`


9. Independent Re-Review Guidance

Suggested focus areas for the next independent reviewer, beyond re-confirming the quality
gates above:
  - Confirm the SET/BOT `basis_sources` URLs are current and the cited guidance figures
    (3-6 months; ~16% p.a.) still match the source pages at review time — these are external
    citations, not code the review can verify purely by static inspection.
  - Confirm `missing_capacity()`'s NOT_APPLICABLE-with-DISCOVERY_CAPACITY_MISSING choice
    (rather than REQUIRE_REVIEW) is the intended fail-closed disposition for R1-04 — this
    was an implementation decision not explicitly specified in the remediation brief, made to
    match the existing NOT_APPLICABLE-for-upstream-unavailable pattern (§43 step 1) since an
    opportunity with unknown capacity is, functionally, not yet actionable upstream data.
  - Confirm the year-scoping rejection in `bundled_financial_policy()` (R1-03c) is acceptable
    scope for this remediation — it was not explicitly requested but was judged necessary to
    make the new temporal-readiness check meaningful (an out-of-year policy would otherwise
    carry a self-contradictory policy_id).
