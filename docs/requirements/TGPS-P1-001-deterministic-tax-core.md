# TGPS-P1-001 — Deterministic Tax Core

**Project:** Tax GPS  
**Repository:** `Tax-GPS`  
**Requirement ID:** `TGPS-P1-001`  
**Phase:** `1.0`  
**Status:** READY FOR IMPLEMENTATION  
**Priority:** P0 / Foundation  
**Target tax year:** 2026 (B.E. 2569)  
**Jurisdiction:** Thailand

## 1. Purpose

Build the first production-grade deterministic tax calculation core for Tax GPS.

This phase must calculate a supported Thai individual taxpayer’s tax state correctly, expose rules/sources/calculation trace, and support deterministic replay.

It must **not** implement recommendation, optimization, UI, AI, fund projection, or product selection.

> No downstream intelligence can compensate for an incorrect tax foundation.

## 2. Product Principle

Tax GPS has the product principle:

> **Best value does not equal maximum tax deduction.**

Phase 1.0 does not yet optimize personal value. Its job is narrower:

> **Calculate tax facts correctly before Tax GPS attempts to make decisions from them.**

## 3. Scope

### 3.1 Core value objects

Implement at minimum:

- `Money`
- `Percentage`
- `TaxYear`

Rules:

- tax/accounting arithmetic MUST use decimal/fixed-point semantics;
- binary floating-point MUST NOT be used for money;
- currency is THB;
- canonical tax year is Gregorian `2026`;
- Buddhist year `2569` is display metadata only.

### 3.2 Versioned Policy Pack

Implement policy loading for tax year 2026.

Tax constants MUST NOT be scattered throughout code.

Separate:

- calculation code;
- policy/configuration.

Each activated material rule MUST contain:

- `rule_id`
- `version`
- `tax_year`
- `effective_from`
- `effective_to` if applicable
- `status`
- `source_id`
- `verified_at`

Recommended lifecycle:

`DRAFT → VERIFIED → EFFECTIVE → SUPERSEDED → EXPIRED`

Runtime must reject a non-approved production policy pack.

### 3.3 Progressive PIT

Implement Thai progressive PIT calculation for the baseline brackets:

| Net taxable income | Rate |
|---:|---:|
| 0–150,000 | Exempt |
| 150,001–300,000 | 5% |
| 300,001–500,000 | 10% |
| 500,001–750,000 | 15% |
| 750,001–1,000,000 | 20% |
| 1,000,001–2,000,000 | 25% |
| 2,000,001–5,000,000 | 30% |
| over 5,000,000 | 35% |

Tax must be calculated progressively.

Tax saving MUST always be authoritative as:

`PIT(before) - PIT(after)`

Never use `deduction × marginal rate` as the authoritative result.

### 3.4 Section 40(1) employment income expense

Support employment income under Section 40(1):

- 50% expense deduction;
- capped at 100,000 THB.

Design should not block later aggregation with Section 40(2), but full 40(2) support is out of scope.

### 3.5 Personal allowance

Support:

- personal allowance = 60,000 THB.

Eligibility and amount logic should remain separable.

### 3.6 Section 33 Social Security — 2026

Support actual employee contribution under applicable 2026 rules:

- contribution rate: 5%;
- wage basis floor: 1,650 THB/month;
- wage basis ceiling: 17,500 THB/month;
- employee monthly maximum: 875 THB/month.

Do NOT hard-code an annual deduction of `9,000`.

The engine must support actual contributions paid.

### 3.7 Existing rights discovery

Implement initial support for:

#### Parent allowance
- 30,000 THB per eligible parent;
- eligibility separate from amount.

#### Child allowance
Model explicitly:
- child order;
- legal eligibility;
- birth year;
- standard allowance;
- additional allowance for eligible second-and-later legal children born from 2018 onward.

#### Mortgage interest
Support:
- actual eligible mortgage interest;
- deduction cap = 100,000 THB.

This is claim discovery only. Taking a mortgage is not an opportunity/recommendation in this phase.

### 3.8 Deduction capacity / shared-limit foundation

Implement generic `DeductionCapacity` supporting:

- standalone limit;
- amount used;
- standalone remaining;
- shared-limit group;
- shared amount used;
- shared remaining;
- usable amount.

Initial shared-limit foundation:

- retirement-related shared group cap = 500,000 THB subject to rule definitions.

Shared-group capacity must be calculated before exposing product-level remaining tax capacity.

Full RMF / Thai ESG recommendation is out of scope.

## 4. Supported Input Boundary

Primary supported taxpayer:

> Thai individual taxpayer with Section 40(1) employment income.

If material unsupported income exists, the engine MUST return an explicit state such as:

- `UNSUPPORTED`
- `ADVANCED_TAX_PATH_REQUIRED`

It MUST NOT silently calculate unsupported income using the salary-only path.

## 5. Required Domain Concepts

Exact names may vary only with a documented architectural reason.

### Core
- `Money`
- `Percentage`
- `TaxYear`

### Profile
- `UserProfile`
- `IncomeProfile`
- `ExistingTaxBenefits`

### Policy
- `RulePack`
- `TaxRule`
- `TaxBracket`
- `LimitGroup`
- `RuleSource`

### Calculation
- `TaxState`
- `IncomeCalculation`
- `ExpenseCalculation`
- `AllowanceCalculation`
- `DeductionCapacity`
- `ExistingRight`

### Trace / audit
- `CalculationStep`
- `CalculationTrace`
- `AuditSnapshot`

## 6. TaxState Output

The engine must expose logically equivalent information to:

```json
{
  "status": "READY",
  "tax_year": 2026,
  "income": {
    "assessable_income": 990500
  },
  "expenses": {
    "section_40_1": 100000
  },
  "allowances": {
    "personal": 60000,
    "social_security": 10500
  },
  "taxable_income": 820000,
  "pit": 79000,
  "marginal_rate": 0.20,
  "existing_rights": [],
  "deduction_capacities": [],
  "calculation_trace": [],
  "rules_applied": [],
  "sources": [],
  "rule_pack": "TH-PIT-2026-...",
  "engine_version": "...",
  "output_hash": "..."
}
```

Exact serialization may differ, but semantics must be preserved.

## 7. Calculation Trace

Every material amount must be explainable.

Example:

```text
Assessable employment income        990,500
- Section 40(1) expense            100,000
- Personal allowance                60,000
- Social Security contribution      10,500
-------------------------------------------
Net taxable income                 820,000
```

Bracket trace:

```text
0 - 150,000                    exempt
150,001 - 300,000 × 5%          7,500
300,001 - 500,000 × 10%        20,000
500,001 - 750,000 × 15%        37,500
750,001 - 820,000 × 20%        14,000
--------------------------------------
PIT                             79,000
```

Each material step should carry:

- `rule_id`;
- `source_id`;
- input amount;
- output amount.

## 8. Determinism

Given identical:

- profile snapshot;
- Rule Pack;
- engine version;

the engine must produce materially identical output.

`same input + same versions = same material result`

No LLM, random input, live market data, current clock dependency, or hidden state may affect Tax Core output.

## 9. Audit Snapshot

Each calculation must be capable of producing an immutable audit snapshot containing at minimum:

- profile version/hash;
- tax year;
- Rule Pack id/version;
- engine version;
- material inputs;
- calculated outputs;
- rules applied;
- calculation trace;
- output hash.

Canonical serialization must be defined before hashing.

Recommended hash: SHA-256.

Same canonical material output must produce the same hash.

## 10. AI Boundary

AI/LLM is OUT of Tax Core.

AI MUST NOT:

- perform tax arithmetic;
- determine eligibility;
- calculate capacities;
- choose tax rules;
- fill missing data;
- modify engine output.

Phase 1 must operate identically without any AI service.

## 11. BPMN / DMN Alignment

Implementation must remain consistent with existing Tax GPS models.

Relevant BPMN areas:

- Tax State Calculation
- Existing Rights Discovery
- Rule Governance
- Audit / Replay

Relevant DMN areas:

- Policy Readiness
- Deduction Capacity

No workflow engine is required in Phase 1.

However:

- service/domain boundaries should map cleanly to BPMN tasks;
- decision logic intended for DMN must not be irreversibly buried in unrelated code;
- any model-semantic change must be reported.

## 12. Mandatory Acceptance Tests

### PIT boundaries

- `0 → 0`
- `150,000 → 0`
- `300,000 → 7,500`
- `500,000 → 27,500`
- `750,000 → 65,000`
- `1,000,000 → 115,000`
- `2,000,000 → 365,000`
- `5,000,000 → 1,265,000`
- `6,000,000 → 1,615,000`

### 40(1) expense

`40(1) income = 100,000 → expense = 50,000`

`40(1) income = 300,000 → expense = 100,000 cap`

### Social Security

`monthly wage = 20,000 → contribution = 875`

`monthly wage = 10,000 → contribution = 500`

### Personal allowance

`eligible taxpayer → 60,000`

### Mortgage

`eligible interest paid = 125,000 → deductible = 100,000`

### Parent

`two eligible parents → 60,000`

### Shared retirement group

Given:

```text
PVD                            400,000
eligible retirement pension   100,000
```

Expected:

`shared retirement remaining = 0`

No later tax-capacity result inside the same group may incorrectly expose positive capacity.

## 13. Golden Personas

### G01 — First Jobber / zero PIT

```text
Annual salary        300,000
40(1) expense        100,000
Personal allowance    60,000
SSO                    10,500
```

Expected:

```text
Taxable income = 129,500
PIT            = 0
```

Any further eligible deduction produces zero current PIT saving.

### G02 — Bracket Crossing

```text
Annual salary        990,500
40(1) expense        100,000
Personal allowance    60,000
SSO                    10,500
```

Expected:

```text
Taxable income = 820,000
PIT            = 79,000
```

Tax-impact test with additional eligible deduction of 100,000:

```text
Taxable after = 720,000
PIT after     = 60,500
Actual saving = 18,500
```

The engine MUST NOT report 20,000.

### G03 — High Income

```text
Annual salary      2,800,000
40(1) expense        100,000
Personal allowance    60,000
SSO                    10,500
```

Expected:

```text
Taxable income = 2,629,500
PIT            = 553,850
```

Tax-impact test with additional eligible deduction 100,000:

```text
Taxable after = 2,529,500
PIT after     = 523,850
Tax saving    = 30,000
```

## 14. Failure / Unsupported Tests

### UNSUPPORTED-01

Material Section 40(8) income with no 40(8) implementation.

Expected:

`ADVANCED_TAX_PATH_REQUIRED`

or equivalent.

Must not silently treat it as 40(1).

### POLICY-01

Rule Pack status = `DRAFT`.

Expected:

Not production-ready / calculation blocked for production use.

### POLICY-02

Material activated rule has no authoritative source metadata.

Expected:

Policy activation fails.

### REPLAY-01

Same input + same engine version + same Rule Pack + same profile snapshot.

Expected:

Same material output hash.

## 15. Testing Requirements

Automated tests required:

### Unit
- Money/value objects
- PIT brackets
- 40(1) expense
- SSO
- allowances
- shared limits
- canonical serialization/hash

### Boundary
- all PIT boundaries

### Golden
- G01–G03
- existing-right fixtures
- shared-limit fixture

### Negative
- invalid negative values where prohibited
- invalid tax year
- unsupported income
- inactive policy
- shared-limit overflow

### Replay
- deterministic hash/replay

## 16. Engineering Constraints

Prefer:

- modular domain boundaries;
- pure/testable domain logic;
- low framework coupling;
- explicit policy/configuration;
- strict typing where supported;
- small modules;
- clear names.

Avoid:

- giant tax service;
- magic numbers;
- scattered constants;
- hidden global state;
- premature generic rules DSL;
- framework-dependent domain objects;
- LLM dependency;
- database dependency for pure arithmetic.

## 17. Out of Scope

Do NOT implement:

- frontend/dashboard;
- mobile app;
- authentication;
- persistent customer database;
- AI assistant;
- recommendation engine;
- “what should I do with 100,000?”;
- Pareto optimizer;
- financial guardrails;
- debt recommendation;
- fund search;
- SEC ingestion;
- investment return projection;
- Monte Carlo;
- Thai ESG/RMF product recommendation;
- insurance product recommendation;
- advisor lead generation;
- payment;
- broker integration;
- tax filing submission;
- corporate tax;
- full 40(2)–40(8).

Do not build future features simply because they may later be useful.

## 18. Required Agent Deliverables

Agent must return:

### A. Implementation
- code;
- policy/config;
- tests;
- documentation updates.

### B. Test report

```text
Tests collected:
Tests passed:
Tests failed:
Coverage:
Golden tests:
Replay tests:
```

### C. Implementation report

Include:

1. Summary
2. Architecture/modules
3. Files changed
4. Requirement coverage mapping
5. Tests and exact commands
6. Tax rule IDs/values/source IDs
7. Deviations from spec
8. Assumptions
9. Open issues
10. BPMN/DMN impact (`NO MODEL CHANGE` or proposed changes)
11. Reproduction commands
12. Git branch / commit SHA / working-tree status

## 19. Definition of Done

TGPS-P1-001 is complete only when:

1. supported 40(1) calculation is deterministic;
2. PIT boundary tests pass;
3. 40(1) expense tests pass;
4. personal allowance works;
5. 2026 SSO handling works;
6. parent/child/mortgage existing-right foundation exists;
7. deduction/shared-limit foundation exists;
8. calculation trace exists;
9. Rule Pack/source provenance exists;
10. unsupported paths fail explicitly instead of approximating;
11. audit hash is deterministic;
12. all mandatory acceptance tests pass;
13. Agent provides implementation report;
14. independent review returns `PASS` or `PASS WITH MINOR ISSUES`.

Until independent review passes:

> **Phase 1.0 is not accepted.**

## 20. Source-of-Truth Policy

Production tax rules must use authoritative sources in this order:

1. Thai law / Royal Gazette;
2. Revenue Department;
3. responsible regulator/government authority;
4. official provider source where relevant.

Blogs, social media, SEO pages, and AI output MUST NOT be tax-policy source-of-truth.

Every implemented material constant must link to source metadata in the Policy Pack.

## 21. Agent Instruction

Implement **only** `TGPS-P1-001`.

Do not continue into later phases without a new requirement.

If a specification conflict is discovered:

1. preserve correctness;
2. document the conflict;
3. do not invent a new product rule silently.

If an authoritative rule is materially ambiguous:

- do not guess;
- isolate the uncertainty;
- report it for review.

The implementation is expected to be boring, deterministic, test-heavy, and auditable.

That is intentional.
