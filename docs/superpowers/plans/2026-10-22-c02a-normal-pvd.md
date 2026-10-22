# C02A Normal PVD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** รองรับภาษีฐานจากเงินสะสม PVD ปกติของผู้มีเงินได้เอง พร้อมหน้าจอไทยที่สรุปก่อนเปิดรายละเอียด.

**Architecture:** เพิ่ม typed facts และ PVD split ใน authoritative baseline เดียว; readiness และ new-cash availability เป็นคนละผลจาก domain. Consumer ทุกตัว replay/version-check ก่อนใช้ผล และหน้าเว็บแสดง baseline-only เมื่อ positive PVD โดยไม่คำนวณกฎหมายเอง.

**Tech Stack:** Python standard library, Money/Decimal, frozen dataclasses; pytest/ruff/mypy (dev only); vanilla HTML/CSS/JS; fresh-server Node tests.

**Spec:** [C02A v0.1](../../requirements/TGPS-C02A-pvd-first-slice.md), [approved UX](../../requirements/TGPS-C02-guided-rights-ux.md), [scoped evidence](../../policy-evidence/2026-10-22/c02a-scope/README.md), DEC-023.

Plan: **APPROVED** (DEC-025); implementation **IN_PROGRESS**. Evidence adequate for planning only; parent C02 remains open. Recommended execution: Native, because these four tasks share the same facts/state/version contracts; final independent review remains required. No execution method chosen on the user's behalf.

## Global Constraints

- Unknown ≠ zero; no preselected true/false. `ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY`.
- Baseline not READY hides PIT/taxable/saving/candidates/export. Positive PVD READY allows baseline export but no new-cash/capacity/saving.
- Positive PVD only one employer/one fund/ordinary2–15%/registered/actual credited money; explicit zero retains prior supported behavior when all facts complete.
- Other rights/history positive remain named unsupported; absence of new paid does not answer history. Own contribution only; no spouse allowance added.
- Salary is gross before PVD exemption; wage basis explicit; allowance≤10000, exemption above10000≤490000, exemption before expense. No statutory constants in adapters/JS.
- Versioned packs/catalogs immutable; runtime stdlib only, no network/clock/random/storage; loopback/allowlist/privacy unchanged. Errors never reflect entered amounts or fund names.
- Coverage100% statements/branches for tax_gps. Tests passing ≠ ACCEPTED. No push/merge authorized by this plan.

## Review Focus

1. Old profile without C02 facts must require input, even if an old snapshot/hash looks valid (Tasks1–2).
2. PVD0 with historical conditional rights must remain blocked; toggling “ไม่มีใหม่” cannot erase history (Tasks1,3).
3. Positive PVD READY must not leak a candidate via a forged READY discovery, tax_impact or old export (Tasks2–3).
4. Payroll deduction not credited / late or paused remittance must get a named scope reason, never a guessed employee disallowance (Tasks1,3).
5. Editing an amount while a response is in flight must hide old results/export and reject late publication (Task3).

## File structure and status

| Task | Responsibility / files | Status |
| --- | --- | --- |
| 1 | New `profile/pvd.py`, `calculation/pvd.py`; modify profile/models.py, calculation/readiness.py, calculation/models.py, engine.py, policy/loader.py; new pack1.1.0; unit/acceptance tests | ⬜ ยังไม่เริ่ม |
| 2 | New calculation/availability.py; modify calculation/models.py, discovery/models.py + engine.py, candidate/activation.py + engine.py, opportunity/loader.py + new catalog1.1.0, audit.py; consumer/version tests | ⬜ ยังไม่เริ่ม |
| 3 | New examples/pvd_adapter.py and examples/web/pvd.js; modify demo_profile.py, web_demo.py, demo_errors.py, web/index.html + app.js + profile.js + profile.css; Python adapter and tests/web/test_app.cjs | ⬜ ยังไม่เริ่ม |
| 4 | Runtime verification, fresh review, progress/decision records; package metadata/version docs if required by changed public contract | ⬜ ยังไม่เริ่ม |

Paths above are relative to src/tax_gps unless prefixed examples/tests/docs. Existing files stay in their current organization; no broad refactor. Preserve unrelated Stage4 draft. Existing feature branch has uncommitted docs; at execution start read using-git-worktrees and verify isolation before code, never stash/reset them.

## Task 1 — Typed facts, readiness, versioned PVD baseline (AC01–05,08)

**Files:** as table; create tests/unit/profile/test_pvd.py, tests/unit/calculation/test_pvd.py, tests/acceptance/test_c02a_pvd.py; modify existing explicit-profile fixture builders and tests/acceptance/test_c01_artifact_versions.py.

**Interfaces — produces:** frozen `PvdFacts` in profile/pvd.py with `employee_paid: Money|None`, `wage_basis: Money|None`, `fund_name: str|None`, and bool|None fields `registered_fund`, `credited_in_tax_year`, `single_employer`, `single_fund`, `ordinary_article_rate`, `normal_remittance`. Zero paid does not require these positive-PVD details. None never means no.

Frozen `OtherRightsFacts` has bool|None for `rmf`, `thai_esg`, `thai_esgx`, `gpf`, `teacher_fund`, `nsf`, `pension_insurance`, `ssf`, `spouse_pvd_claim`, `other_retirement_right`. Frozen `FundHistoryFacts` has bool|None for `prior_conditional_rights`, `disposal_withdrawal_transfer`, `retirement_or_recapture`, `ltf_carryforward`. All required inventory facts must be explicitly false in the supported normal slice. Positive field yields named unsupported; existing advanced-income precedence stays first. Defaults for these objects on ExistingTaxBenefits are None, not synthetic empty confirmations.

`PvdCalculation(employee_paid: Money, allowance: Money, exemption: Money, excess: Money)` frozen in calculation/pvd.py; `calculate_pvd(employee_paid: Money, pack: ActivatedRulePack) -> PvdCalculation` consumes reviewed versioned parameters. Called only after readiness. Extend TaxState with `pvd: PvdCalculation|None`; extend IncomeCalculation with gross-before-exemption and PVD-exemption material fields, keeping `assessable_income` explicitly equal to gross minus PVD exemption. Add `pvd` allowance field and total; all new amounts/inputs enter canonical material/hash and trace.

**Interfaces — consumes:** existing `UserProfile`, `Money`, `ActivatedRulePack`, `BaselineReadiness`. Extend to `assess_baseline(profile: UserProfile, *, pack: ActivatedRulePack) -> BaselineReadiness`; engine.py supplies its activated pack (the only runtime caller found). Readiness inspects new typed facts rather than treating amount_used/shared_usage as paid. Existing positive legacy retirement/shared use remains unsupported. PVD rate check reads inclusive2–15% bounds from the new pack's PVD_NORMAL_SCOPE parameters and uses Decimal comparisons against explicit contribution-period wage basis≤gross salary; no hardcoded statutory bounds or rate clipping. Contradictory paid>0/wage0 or wage>salary is field-specific InvalidValueError, no amounts in text. `normal_remittance=False` is coverage exclusion, not statutory forfeiture.

- [ ] Write AC-linked failing tests: `test_c02a_missing_facts_are_not_zero` asserts missing new object → REQUIRES_INPUT and PIT/taxable None; complete explicit zero → READY. `test_c02a_unknown_and_positive_inventory_precedence` parameterizes every inventory/history field and advanced/unsupported/missing combinations. `test_c02a_zero_does_not_add_employer_restrictions` asserts zero + multi-employer facts retains existing coverage. `test_c02a_actual_credit_and_normal_remittance` asserts None missing, false unsupported with exact fact ID. `test_c02a_normal_rate_and_conflicting_wage` exercises2%,15%, outside limits, zero wage, wage>salary, no amount echo.
- [ ] Add `test_c02a_reference_split_and_order` parameterized from the reviewed normal-reference JSON (9 cases): assert every exemption/allowance/expense/excess/taxable/PIT value, not just PIT. LOW-WAGE asserts expense81500 and taxable11500; SPLIT-10001 expense99999.50; paid600000 claims500000/excess100000. Employer-paid is fixture context only, never mapped into employee_paid or an added deduction. Adapter rejects an unexpected employer_paid key in Task3. Keep old99999 diagnostic distinct from normal fixtures.
- [ ] Run `uv run --locked pytest tests/unit/profile/test_pvd.py tests/unit/calculation/test_pvd.py tests/acceptance/test_c02a_pvd.py -q`; record genuine failing assertions/imports before implementation. Tests already passing are characterization, not RED.
- [ ] Implement interfaces and baseline order; create `TH-PIT-2026-001@1.1.0.json`, retaining1.0.0/1.0.1 bytes. Add rule IDs `PVD_ALLOWANCE`, `PVD_EXEMPTION`, `PVD_NORMAL_SCOPE` with source locators/dates/review notes; loader selects1.1.0 and explicitly accepts historical1.0.0/1.0.1 only by version/hash. ENGINE_VERSION becomes `tax-gps-core/0.3.0`. Add new facts to to_dict/profile hash; current demo profile schema becomes2 in Task3.
- [ ] Migrate every existing supported-profile test fixture to explicit zero + no-rights/history facts, stating AC01 reason in ledger; do not change domain defaults to rescue old tests. Preserve tests whose purpose is missing facts. Run targeted tests then `uv run --locked pytest -q`; all must pass before Task2. Record exact counts/RED→GREEN and mark progress. Make scoped checkpoint only through tgps-git, leaving unrelated changes unstaged.

## Task 2 — Planning availability and replay boundaries (AC06–08)

**Files:** table; create tests/acceptance/test_c02a_consumers.py, extend audit/discovery/candidate and historical artifact tests.

**Interfaces — consumes:** Task1 TaxState.pvd and complete profile. **Produces:** `PlanningAvailability` StrEnum in calculation/availability.py with `AVAILABLE`, `BASELINE_NOT_READY`, `PVD_BASELINE_ONLY`; TaxState `planning_availability: PlanningAvailability` included in material/hash. Domain sets BASELINE_NOT_READY if not READY, PVD_BASELINE_ONLY if positive PVD READY, otherwise AVAILABLE. `TaxState.tax_impact(additional_deduction: Money) -> TaxImpact` keeps existing signature but rejects unavailable planning through existing domain error convention.

Discovery positive-PVD result carries baseline_status READY, reason `PVD_BASELINE_ONLY`, existing PVD right/breakdown and no opportunities/capacities; DiscoveryStatus is UNSUPPORTED for planning only. Do not label baseline unsupported or calculate any percentage-base capacity before checking availability. Consumers expose the same typed reason.

- [ ] Write failing `test_c02a_positive_pvd_baseline_only_all_consumers`: baseline READY/PIT present, availability PVD_BASELINE_ONLY, discovery no new opportunities/capacity, tax_impact rejects, candidate activation/build rejects. `test_c02a_forged_ready_discovery_cannot_activate` changes discovery status/reason/hash and asserts authoritative replay rejects. `test_c02a_zero_retains_candidates` asserts original supported ThaiESG path still works; no nonexistent RMF candidate asserted. `test_c02a_replay_material_and_hash` checks both outputs and hashes, changed paid/availability rejected.
- [ ] Write `test_c02a_historical_bytes_and_current_rejection`: pin existing1.0.0/1.0.1 pack/catalog hashes from HEAD before mutation; explicit old version/hash load works, wrong hashes fail, current loader selects1.1.0, old snapshot engine version rejected. New snapshot exact replay succeeds. Historical replay needs selected compatible historical engine; do not promise current engine reproduces old snapshots.
- [ ] Run `uv run --locked pytest tests/acceptance/test_c02a_consumers.py -q`, observe RED, implement availability checks before calculation/activation and preserve replay checks. New opportunity catalog `TH-OPPORTUNITY-2026-001@1.1.0.json` adds PVD existing-right provenance without new RMF/new-cash treatment; preserve historical bytes. Bump discovery/candidates to0.4.0 and allocation policy to1.1.0 because material/contracts change. Audit keeps profile/pack/engine/hash checks and includes new material via canonical serialization.
- [ ] Run targeted then full Python suite, record counts and fixture migrations. Mark progress/checkpoint as in Task1; availability false must not alter financial guardrail policy or double-charge PVD against new budget.

## Task 3 — Thai guided input and baseline-only HTTP/UI (AC01,05–07,09)

**Files:** table; create tests/acceptance/test_c02a_demo.py; extend tests/web/test_app.cjs using fresh-server wrapper only.

**Interfaces — consumes:** Tasks1–2 domain facts/state/reason IDs. **Produces:** `parse_pvd_profile(value: object) -> tuple[PvdFacts|None, OtherRightsFacts|None, FundHistoryFacts|None]` in examples/pvd_adapter.py. Strict nested profile keys `pvd`, `other_rights`, `fund_history`; string scalars consistent with current adapter: empty→None, true/false explicit, invalid bool/negative/nonfinite/unknown keys rejected privately. Missing group stays None. Amount parsing only; no tax/eligibility calculations. Profile version2 hashes actual submitted facts.

HTTP response adds `planning_availability` and `pvd` breakdown from TaxState. Positive-PVD READY returns baseline/tax state/submitted profile/scope; `financial`, `guardrails`, `outcomes` are null and discovery is the Task2 baseline-only result. It does not parse required budget/assets/expense inputs when planning unavailable. Zero-PVD AVAILABLE retains existing response behavior. NonREADY follows current redacted error response and never serializes partial tax values. Baseline-only export contains only matching baseline facts/trace/provenance/availability; no stale cash plan/selection or fabricated savings.

Browser module exports `collectPvdProfile()`, `renderPvdProfile(data)`, `initPvdProfile(onChange)`, `pvdFieldForFact(factId)`; data matches adapter groups exactly. Use existing 450ms request/version publishing guard. Keep rendering domain decisions in app.js; no legal arithmetic in pvd.js.

- [ ] Write failing `test_c02a_http_missing_zero_positive_and_history` (AC01/05/07): missing facts blocked; explicit zero unchanged; positive normal succeeds without cash inputs but outputs null planning fields; unsupported/history returns named no-tax response. `test_c02a_http_privacy_and_bounds` asserts invalid amount/name never echoed/logged and maximum valid bounded profile fits MAX_BODY; keep4096 if sufficient, otherwise choose smallest documented finite bound after measuring full schema, with over-limit rejection test.
- [ ] Add frontend cases named `C02A unknown input hides every result`, `C02A PVD0 preserves history answers`, `C02A baseline-only shows breakdown and disables new cash`, `C02A edit and late response cannot restore old export`, `C02A error links focus actual required field`. Assert tax summary first, detail collapsed by default, named unsupported item and no empty active comparison tab. Group “ไม่มีทุกข้อ” only sets explicitly visible listed categories; never concealed history.
- [ ] Run Python targeted tests and `uv run --locked python -m examples.check_web_demo` to observe RED with fresh server. Implement adapters/allowlist/pvd.js and UI matching approved prototype: มี/ไม่มี/ยังไม่ทราบ, conditional fields, separate history, readable gross-salary/wage/actual-credited labels and expandable evidence help. No required corporate-accounting questionnaire. Editing clears all publication/export immediately, late/error responses cannot publish. Reference existing profile/css components, no new assets/network/storage.
- [ ] Run targeted/full Python and fresh-server frontend suite; record exact added cases/counts and all skip/fail. Baseline-only export and zero path must both work before Task4.

## Task 4 — Review, rendered checks and delivery (AC09)

- [ ] Read tgps-verify and verification-before-completion. Run all seven AGENTS§4 commands, with fresh-server wrapper and coverage100% statements/branches. Record Python/Node versions, counts and commands in `docs/implementation-reports/TGPS-C02A-progress.md`; any failure remains open.
- [ ] Render actual integrated demo at1440,390,360 and320px, keyboard-only/focus error links, reduced-motion mode and baseline-only/unknown/unsupported/zero states. Capture screenshots and specific interaction observations; prototype screenshots do not count as product QA. Do not terminate unrelated server processes.
- [ ] Use requesting-code-review for one fresh independent final review of this change with spec/plan/ledger and exact diff scope, no unrelated Stage4. Address material findings with RED→GREEN and rerun affected checks; final completion claim requires passing relevant gates after last code change.
- [ ] Mark implementation only with actual evidence and DEC entry; C02 parent not IMPLEMENTED and C01/F09 unchanged. Update requirement/plan/roadmap/README ledger; tests do not mark ACCEPTED. Commit scoped work via tgps-git once reviewed; no push/merge without existing explicit authorization for that action. Report outcome, test counts and remaining acceptance work in Thai.

## Plan self-review

- [x] AC01–05 mapped Task1/3; AC06 Task2; AC07 Task2/3; AC08 Task1/2; AC09 Task4.
- [x] All five Review Focus cases have named owning tests. Shared fact/availability names and response nullability match across tasks.
- [x] No RMF basis, multi-employer aggregation, exceptional rate, ranking, storage or historical-engine implementation is smuggled into this slice.
- [x] Scoped evidence/fixtures reviewed before plan; no RED/GREEN or runtime completion claimed. Plan review and execution choice are still pending.
