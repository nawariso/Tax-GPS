# TGPS-P1-001 Implementation Report

## 1. Summary

Implemented the deterministic Thailand individual tax core defined by
`docs/requirements/TGPS-P1-001-deterministic-tax-core.md` for Gregorian tax year 2026. The
supported path handles Section 40(1) employment income only, uses exact decimal THB arithmetic,
loads a governed policy pack, emits source-backed traces, blocks material unsupported income,
and creates immutable deterministic audit/replay snapshots.

No out-of-scope recommendation, investment-product, persistence, UI, workflow-engine, AI, or
filing behavior was added.

## 2. Architecture and modules

- `tax_gps.core`: immutable `Money`, `Percentage`, and `TaxYear`; isolated exact decimal context;
  canonical UTF-8 JSON and SHA-256.
- `tax_gps.policy`: immutable `RulePack`, `TaxRule`, `TaxBracket`, `LimitGroup`, and `RuleSource`;
  strict JSON loading; Policy Readiness decision; production activation gate; bundled 2026 pack.
- `tax_gps.profile`: immutable `UserProfile`, `IncomeProfile`, `ExistingTaxBenefits`, explicit
  parent/child/retirement inputs, and unsupported-income representation.
- `tax_gps.calculation`: pure PIT, expense, SSO, allowance, existing-right, tax-impact, and
  shared-capacity rules plus immutable result/trace models.
- `tax_gps.engine`: deterministic application service mapping the profile and activated policy
  to `TaxState`.
- `tax_gps.audit`: immutable `AuditSnapshot`, profile hashing, and replay mismatch detection.

The policy-readiness decision and shared-capacity calculation remain isolated so they can map to
the stated DMN decisions without embedding them in workflow or UI code.

## 3. Files changed

- Core: `src/tax_gps/core/*.py`
- Policy: `src/tax_gps/policy/*.py`, `src/tax_gps/policy/packs/TH-PIT-2026-001.json`
- Profile: `src/tax_gps/profile/*.py`
- Calculation/orchestration: `src/tax_gps/calculation/*.py`, `src/tax_gps/engine.py`
- Audit/replay: `src/tax_gps/audit.py`
- Tests: `tests/unit/**`, `tests/acceptance/test_engine.py`, `tests/support/policy.py`
- Provenance/serialization tests: `tests/unit/policy/test_source_provenance.py`,
  `tests/acceptance/test_zero_value_serialization.py`
- Project/docs: `pyproject.toml`, `README.md`, this report, repository metadata files

The repository began as an uncommitted partial RED-stage tree; existing user files were retained
and extended in place.

## 4. Requirement coverage mapping

| Requirement | Implementation | Verification |
|---|---|---|
| Core value objects / decimal-only THB | `core.money`, `core.percentage`, `core.tax_year` | core unit and negative tests |
| Versioned production Rule Pack | `policy.models`, `loader`, `readiness`, `activation`, bundled JSON | loader/readiness tests; POLICY-01/02 |
| Progressive PIT | `calculation.rules.calculate_progressive_pit` | all nine mandatory boundaries |
| Authoritative tax saving | `calculate_tax_saving`; `TaxState.tax_impact` | G01–G03 and 18,500 THB crossing test |
| Section 40(1) expense | `calculate_section_40_1_expense` | 100,000 and 300,000 THB fixtures |
| Personal allowance | explicit `personal_eligible` plus policy amount | eligible/ineligible tests |
| Section 33 SSO | monthly wage calculation plus actual-paid profile amount | 10,000/20,000/floor/zero tests; G01–G03 |
| Parent/child/mortgage discovery | explicit profile models and pure allowance functions | unit fixtures and engine existing-right fixture |
| Generic/shared capacity | `DeductionCapacity`, `LimitGroup`, capacity function, engine group output | 400,000 + 100,000 fixture and overflow tests |
| Supported boundary | `UnsupportedIncome`, `TaxStatus` | UNSUPPORTED-01 and zero-amount control |
| Trace/provenance | `CalculationStep`, `CalculationTrace`, Rule Pack source lookup | trace/source serialization tests |
| Determinism/audit/replay | canonical serialization, profile/output hashes, `AuditSnapshot`, `replay` | REPLAY-01 and mismatch tests |
| AI boundary | no AI/network dependency in runtime | dependency/build inspection |

## 5. Tests and exact commands

Final verification commands:

```console
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run pytest -m mandatory -q
uv run pytest -m golden -q
uv run pytest -m negative -q
uv run pytest -m replay -q
uv run pytest -m boundary -q
uv run ruff check .
uv run mypy
uv build
```

Final recorded results are listed in section 11 after the last clean run.

## 6. Tax rule IDs, values, and source IDs

| Rule ID | Implemented value | Primary source ID |
|---|---|---|
| `TH-PIT-RATE-SCHEDULE` | exempt/5/10/15/20/25/30/35%; boundaries through >5m | `RD-PIT-RATES` |
| `TH-PIT-EXPENSE-40-1` | 50%, capped at 100,000 THB | `RD-EXPENSE-40-1-2026` |
| `TH-PIT-ALLOWANCE-PERSONAL` | 60,000 THB | `RD-RC-SECTION-38-64` |
| `TH-PIT-ALLOWANCE-SSO-33` | 5%; wage floor 1,650, ceiling 17,500, max 875/month; actual paid deductible | `OCS-SSO-WAGE-BASE-2025` |
| `TH-PIT-ALLOWANCE-PARENT` | 30,000 THB per explicitly eligible parent | `RD-RC-SECTION-38-64` |
| `TH-PIT-ALLOWANCE-CHILD` | 30,000 standard + 30,000 for eligible legal child order ≥2 born ≥2018 | `RD-RC-SECTION-38-64` |
| `TH-PIT-ALLOWANCE-MORTGAGE-INTEREST` | actual eligible interest, capped at 100,000 THB | `RD-MORTGAGE-2025-INSTRUCTIONS` |
| `TH-PIT-LIMIT-RETIREMENT-SHARED` | generic shared group cap 500,000 THB | `RD-RMF-FAQ` |

Official metadata and retrieval dates are stored in the bundled pack. Key official URLs:

- Revenue Department rate schedule: <https://www.rd.go.th/5938.html>
- Revenue Code Sections 38–64: <https://www.rd.go.th/5937.html>
- Revenue Department 2026 expense guide:
  <https://rd.go.th/fileadmin/user_upload/callcenter/Q_A___Easy_Tax/Taxdeduct69.pdf>
- Office of the Council of State law index (B.E. 2568, vol. 142, part 81 A, page 5):
  <https://www.ocs.go.th/searchlaw/law-index/?page=4>
- Royal Thai Government cabinet summary for the phased Section 33 wage base:
  <https://www.thaigov.go.th/uploads/document/235/2025/12/pdf/20251202192323_4506.pdf>
- Revenue Department tax-year 2025 P.N.D.90 instructions:
  <https://www.rd.go.th/fileadmin/tax_pdf/pit/2568/Ins90_241268.pdf>
- Revenue Department RMF/PVD FAQ: <https://www.rd.go.th/60059.html>
- Royal Decree (No. 470) B.E. 2551 granting the 0–150,000 THB exemption:
  <https://www.rd.go.th/33893.html>
- Revenue Department bracket table effective from tax year 2560:
  <https://www.rd.go.th/fileadmin/user_upload/borkor/tax121260.pdf>
- Revenue Department published allowance schedule:
  <https://www.rd.go.th/fileadmin/download/tax_deductions_update30072567.pdf>

### Source verification performed

Every source URL in the pack was fetched and returned HTTP 200. The following constants were
read directly out of the official documents rather than assumed:

- **PIT brackets:** the Revenue Code rate schedule (`rd.go.th/5938.html`) was retrieved and
  confirms 5/10/15/20/25/30/35% at the implemented thresholds. That schedule *begins at
  300,000 THB* and does **not** itself grant the first-150,000 exemption; Royal Decree
  (No. 470) B.E. 2551 does. Both are now cited, and
  `tests/unit/policy/test_source_provenance.py` fails if that decree citation is ever dropped.
- **Section 33 wage base:** the cabinet document was parsed and states that for B.E.
  2569–2571 (2026–2028) the maximum wage base is 17,500 THB, the minimum remains 1,650 THB,
  and the rate remains 5% — giving the implemented 875 THB monthly maximum.
- **Allowances:** the published Revenue Department allowance schedule was parsed and confirms
  personal 60,000, parent 30,000 each, child 30,000, housing-loan interest capped at 100,000,
  social security deductible "as actually paid", and the 500,000 THB combined retirement
  ceiling.

The 2026 expense PDF (`Taxdeduct69.pdf`) is a scanned document with no text layer, so the
50% / 100,000 THB Section 40(1) expense rule could not be machine-verified from it; it is
additionally cited to the Revenue Code.

## 7. Deviations from specification

- Exact class/concept names requested by section 5 are present; no architectural renames were
  needed.
- `ADVANCED_TAX_PATH_REQUIRED` is used for material unsupported income, one of the explicitly
  permitted equivalent statuses.
- The serialized output adds `rule_pack_version` and `unsupported_reasons`; these make replay and
  failure states explicit without changing required semantics.
- Existing retirement contributions affect shared capacity only. They are not subtracted from
  taxable income because product-specific eligibility and full RMF/pension implementation are
  out of scope.

## 8. Assumptions

- All eligibility facts are authoritative caller inputs. The engine does not infer age, study,
  dependency, legal relationship, duplicate claims, lender qualification, residence use, or
  retirement-product eligibility.
- `social_security_paid` is the actual employee contribution paid during the tax year and is used
  as supplied after non-negative validation. The monthly helper separately demonstrates the 2026
  statutory wage basis and rate.
- A zero-valued unsupported-income entry is non-material and does not block the supported path;
  any positive amount does.
- Policy verification and source retrieval date is 2026-09-15.

## 9. Open issues and reported ambiguities

These are deliberately not resolved by invented rules:

1. **Tax rounding:** the requirement mandates decimal/fixed-point semantics but gives no rule for
   rounding fractional satang in derived PIT. The engine preserves the exact decimal result and
   performs no implicit rounding.
2. **Annual SSO reconciliation:** the requirement supports actual contributions but does not
   define treatment of refunds, payroll corrections, partial months, or an annual validation
   ceiling. The engine accepts a non-negative actual-paid aggregate and does not invent those
   rules.
3. **Eligibility evidence:** the requirement gives amounts but not complete statutory eligibility
   tests for parents, children, or mortgages. Eligibility is explicit input and is never inferred.
4. **Mortgage source timing:** as of verification, the official Revenue Department instructions
   available for filing substantiate the 100,000 THB cap for tax year 2025; a separate tax-year
   2026 filing instruction was not identified. The policy records this limitation and also links
   the Revenue Code.
5. **Retirement composition:** the requirement defines a 500,000 THB shared foundation but leaves
   product-specific definitions, percentage limits, ordering, and eligibility out of scope. The
   engine therefore reports generic shared capacity only.
6. **Section 40(1) expense source for 2026:** the Revenue Department's 2026 expense/deduction
   summary is published as a scanned PDF without a text layer, so the 50% / 100,000 THB rule
   could not be machine-verified from that document. The value is long-standing and is also
   cited to the Revenue Code, but a human should confirm it against the 2026 filing
   instructions when those are published.
7. **Child-count restriction:** the published allowance schedule limits adopted/non-legitimate
   children to three. The requirement does not ask for a count restriction in this phase, so it
   is recorded in the rule's review notes and deliberately not enforced.
8. **Parent statutory conditions:** the published schedule conditions the parent allowance on a
   parent aged 60 or over with assessable income not exceeding 30,000 THB. The requirement keeps
   eligibility separate from amount, so those conditions remain caller-asserted inputs and are
   never inferred.

## 10. BPMN / DMN impact

`NO MODEL CHANGE`.

Boundaries remain aligned with Tax State Calculation, Existing Rights Discovery, Rule Governance,
Audit/Replay, Policy Readiness, and Deduction Capacity. No workflow engine or altered process
semantics were introduced.

## 11. Reproduction commands and final test report

```text
Tests collected: 238
Tests passed: 238
Tests failed: 0
Coverage: 100% statements, 100% branches
Mandatory tests: 22 passed
Boundary tests: 9 passed
Golden tests: 5 passed
Negative tests: 87 passed
Replay tests: 7 passed
```

`uv build` succeeds, producing `tax_gps_core-0.1.0.tar.gz` and `tax_gps_core-0.1.0-py3-none-any.whl`.

Use the exact commands in section 5 from the repository root.

### Independent review

An independent reviewer with no implementation context re-derived all nine PIT boundaries, both
Section 40(1) expense cases, both social-security cases, and personas G01–G03 from the
specification, and audited determinism, policy governance, the unsupported path, and scope.

Verdict: **PASS** — no spec violations, logic errors, out-of-scope features, or security
concerns. Three non-blocking suggestions were raised; their disposition:

1. *No sanity cap on actual social-security contributions.* Not changed. Specification 3.6
   mandates actual contributions paid and explicitly forbids hard-coding an annual figure;
   inventing a ceiling would be a fabricated tax rule. Recorded as open issue 2.
2. *Retirement group passes the same amount as standalone and shared usage.* Not changed. The
   mandatory fixture result is correct and product sublimits are out of scope; the standalone
   dimension becomes meaningful only when per-product rules arrive. Recorded as open issue 5.
3. *Optional material amounts guarded by truthiness.* **Fixed.** `calculation/models.py` now
   uses explicit `is not None`. This was verified as a real latent hazard, not a style point: a
   temporary `Money.__bool__` probe made a legitimate zero PIT serialize as `null` — corrupting
   the audit hash and making a zero-tax taxpayer indistinguishable from an unsupported
   calculation. `tests/acceptance/test_zero_value_serialization.py` now pins the contract and
   was confirmed to fail under the old code and pass under the fix.

## 12. Git branch, commit SHA, and working-tree status

- Branch: `main`
- Commit SHA: `29aee6258a67a442aa4464009f16b2786993c3da` (initial commit on `main`)
- Working tree: clean at the time of commit
- Push: not performed; `origin` (github.com/nawariso/Tax-GPS) is configured but the remote
  `main` is reported as gone, so pushing is left to the repository owner

Independent review result: **PASS**.
