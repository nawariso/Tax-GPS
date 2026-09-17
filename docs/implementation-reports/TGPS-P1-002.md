# TGPS-P1-002 Implementation Report

## 1. Summary

Implemented the Phase 1.1 deterministic existing-right and tax-opportunity discovery engine for
Thailand tax year 2026. The engine consumes the accepted `tax-gps-core/0.1.1` tax state, reports
existing rights before new-cash opportunities, exposes explicit eligibility/readiness states,
calculates legal capacity and tax impact through the accepted Tax Core, and creates deterministic
discovery audit snapshots with replay verification.

The implementation does not rank, recommend, optimize, select products, project returns, or add a
frontend, API, database, workflow engine, filing path, advisor routing, or AI decision path.

## 2. Architecture and modules

- `tax_gps.opportunity.models`: immutable catalog, definition, rule, evidence, lockup, type,
  category, and status concepts.
- `tax_gps.opportunity.loader`: strict JSON loading, exact-key validation, decimal-only constants,
  duplicate rejection, and source/rule/reference validation.
- `tax_gps.opportunity.readiness` and `activation`: fail-closed policy readiness and catalog
  activation.
- `tax_gps.opportunity.catalogs.TH-OPPORTUNITY-2026-001.json`: versioned Thailand 2026 catalog.
- `tax_gps.discovery.context`: explicit tax year and planning date; no system-clock dependency.
- `tax_gps.discovery.intent`, `effective_period`, `eligibility`, and `capacity`: isolated pure
  decisions.
- `tax_gps.discovery.engine`: deterministic existing-right-first orchestration and source/rule
  resolution.
- `tax_gps.discovery.models`: immutable results, stable reason codes, canonical serialization.
- `tax_gps.discovery.audit`: profile/catalog/context hashes, immutable snapshot, and replay.
- `tax_gps.profile.models`: explicit opportunity facts, intrinsic intent, shared-limit usage, and
  structural duplicate validation.

## 3. Requirement coverage

| Requirement | Implementation | Verification |
|---|---|---|
| Existing rights before new spending | Fixed `EXISTING_RIGHT_IDS` order; separate `existing_rights` and `opportunities` result groups | DISC-01 and ordering tests |
| Versioned opportunity catalog | Strict immutable catalog and bundled `TH-OPPORTUNITY-2026-001` JSON | Loader, schema, activation, duplicate, and canonical-hash tests |
| Explicit states | `AVAILABLE`, `INELIGIBLE`, `REQUIRES_INPUT`, `RULE_NOT_READY`, `OUTSIDE_EFFECTIVE_PERIOD` | Mandatory and negative acceptance tests |
| Existing/new-cash economic type | `OpportunityType.EXISTING_RIGHT` and `NEW_CASH`; `requires_new_cash` | Type and serialization tests |
| Intrinsic intent | Explicit artwork and solar intent gates; unknown remains missing input | DISC-08/09/13 and decision tests |
| Missing-input semantics | Tri-state facts; no assumed eligibility | Missing/failed-fact acceptance and unit tests |
| Shared limits | Thai ESG/Thai ESGX usage shares `THAI_ESG_2026_POOL`; capacity floors at zero | DISC-04/05/06 plus zero-income regression |
| Effective dates | Explicit `DiscoveryContext`; pure inclusive period decision | DISC-16 and decision boundary tests |
| Tax impact | Accepted `TaxState.tax_impact`, using `PIT(before) - PIT(after)` | DISC-18/19 and zero-current-benefit tests |
| Provenance | Rule/source IDs resolved in deterministic first-reference order | Catalog/readiness and result provenance tests |
| Audit/replay | Canonical profile, policy, catalog, context, tax-state, and output hashes | Replay mutation and determinism tests |
| Structural duplicates | Parent role, child ID/order, retirement product, and shared-usage group rejection | Profile structural-validation tests |
| No ranking/recommendation | No rank, score, best, priority, recommendation, or spend directive in result models | DISC-20 and capacity-framing test |

## 4. Bundled opportunity policy posture

### Thai ESG 2026

The active rule implements a capacity ceiling equal to the lower of 30% of assessable income and
THB 300,000, reduced by caller-supplied 2026 Thai ESG/Thai ESGX shared-pool usage. Five-year
purchase-date-to-purchase-date holding metadata is exposed. The active source is official SEC
Thailand guidance.

The underlying Revenue Department instrument for the 2026 Thai ESG/Thai ESGX shared pool was not
retrieved. The catalog therefore records that no independent Thai ESGX opportunity is exposed;
Thai ESGX can only conservatively consume capacity supplied by the caller. This unresolved source
layer is recorded as an ambiguity rather than silently represented as separately verified policy.

### Artwork purchases

The catalog preserves the THB 100,000 metadata, 2025-01-01 through 2027-12-31 period, qualifying
seller/artwork/document evidence requirements, and intrinsic-intent gate. The underlying
Ministerial Regulation and Director-General notification were not verified in authoritative full
text. The bundled rule remains `DRAFT` with `verified_at: null`; production discovery returns
`RULE_NOT_READY` before calculating capacity or tax saving.

### Solar Rooftop — Royal Decree No. 805

The catalog preserves the official Revenue Department decree and press-release sources, THB
200,000 metadata, residential/grid/VAT/e-tax/non-duplication evidence requirements, one-system
metadata, and intrinsic-intent gate. The decree body could not be fully text-verified for every
material ownership and installation condition. The bundled rule remains `DRAFT` with
`verified_at: null`; production discovery returns `RULE_NOT_READY` before capacity or tax saving.

An explicit caller statement that artwork or solar is not intrinsically intended returns
`INELIGIBLE / NO_INTRINSIC_NEED`; this is a user-intent fact, not an inference from unverified tax
policy. Effective-period and intent gates precede readiness, so a not-ready rule can also return
`OUTSIDE_EFFECTIVE_PERIOD` or `NO_INTRINSIC_NEED`; none of those paths can return `AVAILABLE`.

## 5. Determinism and fail-closed behavior

- Discovery receives `DiscoveryContext` explicitly and never reads the clock.
- Catalog order, rule order, source order, reason order, and result groups are deterministic.
- Canonical JSON and SHA-256 cover all material discovery output.
- Replay verifies profile, tax state, Rule Pack, catalog, context, engine version, frozen result,
  and discovery hash.
- Unknown material facts produce `REQUIRES_INPUT`.
- Failed eligibility facts produce `INELIGIBLE` and identify exact failed fact IDs.
- Missing/unverified/non-effective/unresolved rules produce `RULE_NOT_READY`.
- Artwork and solar cannot become available from the bundled production catalog.
- Capacity is described as a legal tax-treatment ceiling, never an instruction to spend.

## 6. Verification commands and results

Commands executed from the repository root:

```console
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run pytest -m mandatory -q
uv run pytest -m boundary -q
uv run pytest -m golden -q
uv run pytest -m negative -q
uv run pytest -m replay -q
uv build
```

Final local results on CPython 3.14.3:

```text
Tests collected: 353
Tests passed: 353
Tests failed: 0
Coverage: 100% statements, 100% branches
Mandatory tests: 50 passed
Boundary tests: 9 passed
Golden tests: 10 passed
Negative tests: 123 passed
Replay tests: 15 passed
Ruff lint: passed
Ruff format check: passed
Mypy strict: passed (67 source files)
Build: passed
Artifacts: tax_gps_core-0.1.1.tar.gz, tax_gps_core-0.1.1-py3-none-any.whl
```

A local Python 3.12 interpreter was not installed, and `--no-python-downloads` correctly failed
closed rather than silently substituting 3.14. The repository CI explicitly provisions and
asserts Python 3.12. The Python 3.12 gate remains pending until the pushed commit's GitHub Actions
run completes.

## 7. Independent review

Two independent reviews inspected the actual staged artifact.

Initial code/spec verdict: **PASS WITH MINOR ISSUES**. No correctness, fail-closed, determinism,
replay, scope, or test-independence defect was found. The reviewer identified:

1. `SHARED_LIMIT_APPLIED` was emitted for a zero-capacity Thai ESG result even when shared usage
   was zero and income alone caused zero capacity. Fixed by requiring positive shared usage.
2. Retirement remaining capacity used `deduction_capacities[0]`. Fixed by matching the
   definition's `shared_limit_group` and falling back to zero when absent.
3. Intent/effective-period precedence over policy readiness was informational and retained; it is
   deliberate, test-covered, and cannot produce `AVAILABLE` from an unready rule.

Both fixes were developed with regression tests that were observed failing before the production
change and passing afterward. A focused independent re-review inspected the fixes and returned
**PASS** with no remaining findings.

The independent legal-policy review returned **PASS WITH MINOR ISSUES**. It confirmed that artwork
and solar fail closed end to end and that no ranking/recommendation semantics leak into output. It
identified two residual provenance-transparency limitations, recorded rather than hidden:

- the active shared Thai ESG/Thai ESGX pool has official SEC guidance but no retrieved underlying
  Revenue Department instrument;
- rule review notes are catalog governance metadata and are not copied into each discovery result;
  consumers receive `RULE_NOT_READY`, rule/source IDs, and authoritative source metadata, while
  the detailed full-text-verification caveat remains in the versioned catalog and this report.

Overall implementation verdict after remediation: **PASS**. Legal-policy provenance verdict:
**PASS WITH MINOR ISSUES**, with the two limitations above remaining explicit.

## 8. Deviations and ambiguities

- No ranking, recommendation, optimizer, projection, guardrail, UI, API, persistence, filing,
  advisor-routing, or AI feature was added.
- Exact required domain concepts are represented. Names differ only where the existing codebase
  already distinguishes calculation status (`DiscoveryStatus`) from per-opportunity eligibility
  (`OpportunityStatus`).
- Test-only helpers can activate draft artwork/solar rules to verify evaluator behavior; the
  bundled production catalog cannot.
- Complete primary legal text remains unresolved for artwork and for several solar conditions.
  Those rules remain inactive rather than relying on secondary reporting.
- The Thai ESG/Thai ESGX shared-pool source gap is conservative in this phase: caller-supplied
  Thai ESGX use can only reduce Thai ESG capacity, and no Thai ESGX opportunity is offered.

## 9. BPMN / DMN impact

`NO BUSINESS PROCESS CHANGE`.

The implementation keeps Policy Readiness, Effective Period, Intrinsic Intent, Eligibility, and
Deduction Capacity as isolated decisions suitable for later DMN mapping. No workflow engine or
future recommendation process was introduced.

## 10. Git state

- Accepted Phase 1.0 tag: `v0.1.1` at `c949e50fe23f82a26cb9fc50dfc668de74f0cc7d`
- Feature branch: `feature/tgps-p1-002-opportunity-discovery`
- Verified implementation commit: `5bbdd8e7061876bf6d86ad3ac3be2d6a3bf2bb55`
- Publication and Python 3.12 CI evidence: pending push at the time this report was authored
