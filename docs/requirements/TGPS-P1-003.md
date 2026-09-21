# TGPS-P1-003 — Financial State & Guardrails

**Project:** Tax GPS
**Repository:** `nawariso/Tax-GPS`
**Requirement ID:** `TGPS-P1-003`
**Phase:** `1.2 — Financial Safety Foundation`
**Status:** READY FOR IMPLEMENTATION
**Priority:** P0
**Parent:** `TGPS-P1-002 — Existing Rights & Opportunity Discovery`
**Jurisdiction:** Thailand
**Target Tax Year:** 2026 / B.E. 2569

---

## 1. Purpose

Extend Tax GPS from:

```text
Tax State
    ↓
Existing Rights
    ↓
Eligible Opportunities
```

to:

```text
Tax State
    ↓
Existing Rights
    ↓
Eligible Opportunities
    ↓
Financial State
    ↓
Financial Guardrails
    ↓
Feasible / Restricted Opportunities
```

The purpose of this phase is to answer:

> Given an opportunity that is legally available, is allocating new cash to it financially safe for this user?

This phase does **not** answer:

> Which opportunity is best?

Ranking and optimization are explicitly deferred.

---

## 2. Accepted Baseline

Implementation must start from merged `main` containing:

```text
eaaf3410a18db2e2501a76563e3a89d4e7186c8f
```

Baseline verification already completed:

```text
384 tests passed
0 failed

100% statement coverage
100% branch coverage

ruff check: PASS
ruff format --check: PASS
mypy --strict: PASS
uv build: PASS
```

Implementation branch:

```text
feature/tgps-p1-003-financial-guardrails
```

Do not rewrite accepted history.

---

## 3. Core Product Principle

Tax GPS must enforce:

> **Tax efficiency must never override basic financial safety.**

Therefore:

```text
Tax deduction available
≠
financially appropriate to use it
```

and:

```text
Maximum tax capacity
≠
recommended allocation
```

This layer sits between Discovery and future Optimization.

---

## 4. Decision Precedence

Mandatory precedence:

```text
1. Legal / Tax Rule Validity
2. Discovery Eligibility
3. Financial Data Validity
4. Hard Financial Safety
5. Liquidity Preservation
6. User Intent
7. Feasibility
8. Optimization — FUTURE
```

A downstream financial rule must never make an upstream unavailable opportunity become available.

---

## 5. Architecture Boundary

Target architecture:

```text
UserProfile
    │
    ├── Tax / Discovery facts
    │
    └── FinancialProfile
              │
              ▼
        FinancialState
              │
DiscoveryResult
              │
              ▼
        Guardrail Engine
              │
              ▼
        GuardrailResult
```

Keep these layers separate:

```text
Tax Engine
≠
Discovery Engine
≠
Financial State Engine
≠
Guardrail Engine
```

Do not create a giant orchestration/service object containing all business logic.

---

## 6. Scope

Implement:

1. `FinancialProfile`
2. deterministic `FinancialState`
3. versioned Financial Guardrail Policy
4. Guardrail Engine
5. deterministic Guardrail Result
6. audit snapshot and replay
7. tests and CI evidence

---

## 7. Explicitly Out of Scope

Do NOT implement:

```text
recommendation ranking
best option
weighted scoring
Pareto optimization
candidate portfolio optimization
specific fund selection
specific insurance recommendation
expected investment return
market data ingestion
wealth projection
Monte Carlo
debt repayment optimizer
loan refinance recommendation
advisor routing
AI decision making
frontend
API server
database persistence
```

---

# Financial Profile

## 8. FinancialProfile

Introduce logically equivalent domain concepts:

```text
FinancialProfile
├── liquid_assets
├── monthly_essential_expenses
├── debts[]
├── committed_cash_needs[]
└── protection
```

Financial facts must be caller supplied.

---

## 9. Liquid Assets

```text
liquid_assets: Money | None
```

Represents near-term accessible money such as:

```text
cash
bank deposits
cash-equivalent balances
```

Do not automatically include:

```text
retirement funds
locked investments
illiquid property
insurance surrender value
```

Unknown must remain `None`.

---

## 10. Monthly Essential Expenses

```text
monthly_essential_expenses: Money | None
```

Validation:

```text
>= 0
```

Do not infer expenses from salary.

Unknown ≠ zero.

---

## 11. Debt

Introduce:

```text
Debt
├── debt_id
├── category
├── outstanding_balance
├── annual_percentage_rate
├── minimum_monthly_payment
└── secured
```

Supported categories should include at minimum:

```text
CREDIT_CARD
PERSONAL_LOAN
CASH_CARD
AUTO_LOAN
MORTGAGE
STUDENT_LOAN
OTHER
```

Debt category must not determine cost by itself.

APR is the guardrail input.

---

## 12. APR

Use Decimal/fixed-point semantics.

No binary float.

Example:

```text
0.1800 = 18.00% p.a.
```

Validate:

```text
APR >= 0
```

Do not invent an upper bound without policy justification.

---

## 13. Committed Cash Need

Introduce:

```text
CommittedCashNeed
├── need_id
├── amount
├── due_date
├── mandatory
└── description
```

Examples:

```text
tuition
known medical payment
home down payment
scheduled family obligation
other known mandatory expense
```

These are actual planned cash requirements, not aspirational goals.

---

## 14. ProtectionProfile

Minimum model:

```text
ProtectionProfile
├── required_life_coverage
└── existing_life_coverage
```

Both:

```text
Money | None
```

Do not invent required coverage.

If both are known:

```text
protection_gap
=
max(
  required_life_coverage
  -
  existing_life_coverage,
  0
)
```

If required coverage is unknown:

```text
protection_gap = UNKNOWN
```

---

## 15. No Financial Inference

The engine MUST NOT infer:

```text
expenses from salary
APR from debt category
protection need from age
protection need from dependents
liquid assets from income
cash commitments from unrelated profile data
```

Invariant:

> **Unknown ≠ zero ≠ false**

---

# Financial State

## 16. FinancialState

Introduce logically equivalent:

```text
FinancialState
├── status
├── liquid_assets
├── monthly_essential_expenses
├── emergency_fund_months
├── emergency_reserve_floor
├── emergency_reserve_target
├── near_term_committed_cash
├── protected_liquidity
├── spendable_surplus
├── critical_debt_balance
├── critical_debt_ids[]
├── protection_gap
├── reason_codes[]
├── policy_id
├── policy_version
└── state_hash
```

---

## 17. Emergency Fund Policy

Initial product-policy values:

```text
Emergency Floor  = 3 months
Emergency Target = 6 months
```

These are **Tax GPS product financial policy**, not statutory tax law.

When inputs are known:

```text
emergency_fund_months
=
liquid_assets
/
monthly_essential_expenses
```

---

## 18. Zero Expense Handling

If:

```text
monthly_essential_expenses = 0
```

do not divide by zero.

Represent the result explicitly.

Possible acceptable semantics:

```text
emergency_fund_months = null
```

with deterministic reason code such as:

```text
ZERO_ESSENTIAL_EXPENSE_BASE
```

Do not use artificial infinity in serialized material output unless strongly justified.

---

## 19. Emergency Reserve

Calculate:

```text
emergency_reserve_floor
=
monthly_essential_expenses × 3
```

and:

```text
emergency_reserve_target
=
monthly_essential_expenses × 6
```

Only the 3-month floor is a hard guardrail in v0.1.

The 6-month figure is informational.

---

## 20. Near-Term Liquidity Horizon

Initial policy:

```text
12 months
```

from explicit `planning_date`.

Calculate:

```text
near_term_committed_cash
=
sum(
  mandatory cash needs
  due within the configured horizon
)
```

Boundary must be documented and deterministic.

Prefer:

```text
planning_date <= due_date <= horizon_end
```

Do not use system time.

---

## 21. Protected Liquidity

Calculate:

```text
protected_liquidity
=
emergency_reserve_floor
+
near_term_committed_cash
```

Then:

```text
spendable_surplus
=
max(
  liquid_assets - protected_liquidity,
  0
)
```

`spendable_surplus` is a financial feasibility value.

It is NOT a spending recommendation.

---

# Planning Context

## 22. FinancialPlanningContext

Introduce:

```text
FinancialPlanningContext
├── planning_date
└── available_budget
```

`available_budget` means:

> current liquid money the user is considering allocating.

Validation:

```text
available_budget >= 0
```

If liquid assets are known:

```text
available_budget <= liquid_assets
```

Otherwise fail validation/fail closed.

---

# Financial Guardrail Policy

## 23. Versioned Policy

Create a versioned artifact logically equivalent to:

```text
TH-FIN-GUARDRAIL-2026-001
```

Fields:

```text
policy_id
version
status
effective_from
effective_to

emergency_floor_months
emergency_target_months

critical_debt_apr

near_term_liquidity_months

basis_sources[]
review_notes[]
```

Initial policy:

```text
emergency_floor_months = 3
emergency_target_months = 6
critical_debt_apr = 0.15
near_term_liquidity_months = 12
```

---

## 24. Policy Classification

Financial guardrail values are:

```text
PRODUCT_FINANCIAL_POLICY
```

They are not tax/legal rules.

Do not represent:

```text
3 months
6 months
15%
12 months
```

as statutory requirements.

---

## 25. Policy Basis

Document provenance separately.

Financial planning basis:

```text
Emergency savings guidance:
approximately 3–6 months of expenses
```

Debt context:

```text
Thai credit-card interest/fees can reach approximately 16% p.a.
```

Tax GPS decision:

```text
critical_debt_apr = 15%
```

The 15% threshold is an internal conservative product-safety policy.

It is not a Bank of Thailand regulatory threshold.

---

## 26. Policy Readiness

Financial policy must fail closed if:

```text
DRAFT
UNAPPROVED
EXPIRED
INVALID
missing required parameter
invalid source metadata
```

Guardrail evaluation requiring that policy must return conceptually:

```text
POLICY_NOT_READY
```

Do not silently substitute code defaults.

---

# Critical Debt

## 27. Critical High-Cost Debt

Initial classification:

```text
APR >= 15%
```

Calculate:

```text
critical_debt_balance
=
sum(
  debt.outstanding_balance
  where debt.APR >= policy.critical_debt_apr
)
```

and:

```text
critical_debt_ids[]
```

Ordering must be deterministic.

---

# Guardrail Decisions

## 28. Decision Enum

At minimum:

```text
ALLOW
BLOCK
CAP
REQUIRE_REVIEW
```

Reserve:

```text
PENALIZE
```

for future optimizer integration.

Do not implement numeric penalties in this requirement.

---

## 29. Upstream Status

If Discovery status for an opportunity is:

```text
RULE_NOT_READY
REQUIRES_INPUT
INELIGIBLE
OUTSIDE_EFFECTIVE_PERIOD
```

guardrails must not override it.

Output conceptually:

```text
guardrail_status = NOT_APPLICABLE
decision = null
reason = UPSTREAM_NOT_AVAILABLE
```

Financial logic must never promote an unavailable tax opportunity.

---

## 30. Existing Rights

Existing rights require no new spending.

Therefore:

```text
EXISTING_RIGHT
→ ALLOW
```

Financial conditions must never block:

```text
personal allowance
parent allowance
child allowance
social security right
mortgage-interest right
existing retirement capacity/right presentation
```

---

## 31. Independent Feasibility Ceiling

For an `AVAILABLE` new-cash opportunity:

```text
max_feasible_allocation
=
min(
  discovery.remaining_capacity,
  planning_context.available_budget,
  financial_state.spendable_surplus
)
```

This is a **single-opportunity independent ceiling**.

It must NOT be interpreted as an amount that should be invested.

Do not add ceilings across opportunities as if they could all be funded simultaneously.

That belongs to Candidate Allocation / Optimization.

---

# Guardrail Matrix

## 32. Critical Debt + Investment Tax

If:

```text
critical debt exists
AND
category = INVESTMENT_TAX
AND
requires_new_cash = true
```

then:

```text
decision = BLOCK
max_feasible_allocation = 0
reason = CRITICAL_DEBT_PRESENT
```

Example:

```text
18% debt
+
Thai ESG
```

must not pass simply because Thai ESG reduces tax.

---

## 33. Critical Debt + Intrinsic-Purpose Opportunity

For categories such as:

```text
UTILITY_INVESTMENT
LIFESTYLE_INTENT
```

with genuine user intent:

```text
decision = REQUIRE_REVIEW
```

Do not automatically `ALLOW`.

Do not automatically `BLOCK`.

This preserves user agency.

---

## 34. Emergency Fund Below Floor

If:

```text
liquid_assets < emergency_reserve_floor
```

then for:

```text
INVESTMENT_TAX
```

return:

```text
BLOCK
max_feasible_allocation = 0
EMERGENCY_FUND_BELOW_FLOOR
```

---

## 35. Emergency Shortfall + Intrinsic Purpose

For genuine:

```text
UTILITY_INVESTMENT
LIFESTYLE_INTENT
```

when below emergency floor:

```text
REQUIRE_REVIEW
```

Do not let the tax dimension decide the user's underlying purpose.

---

## 36. Liquidity Cap

If:

```text
0
<
spendable_surplus
<
min(
  available_budget,
  discovery.remaining_capacity
)
```

and no stronger rule applies:

```text
decision = CAP
max_feasible_allocation = spendable_surplus
reason = ALLOCATION_CAPPED_BY_LIQUIDITY
```

---

## 37. No Spendable Surplus

If:

```text
spendable_surplus = 0
```

and no stronger condition applies:

For `INVESTMENT_TAX`:

```text
BLOCK
```

For intrinsic-purpose opportunities:

```text
REQUIRE_REVIEW
```

Reason:

```text
NO_SPENDABLE_SURPLUS
```

---

## 38. Healthy State

When:

```text
upstream opportunity AVAILABLE
policy READY
financial inputs complete
no critical debt
emergency fund >= floor
no conflicting mandatory liquidity
spendable surplus sufficient
```

return:

```text
ALLOW
```

with:

```text
max_feasible_allocation
=
min(
  available_budget,
  tax capacity,
  spendable surplus
)
```

---

# Protection

## 39. Protection Gap

If known:

```text
required coverage = 3,000,000
existing coverage = 1,000,000
```

then:

```text
protection_gap = 2,000,000
```

Expose:

```text
PROTECTION_GAP
```

In `P1-003`, protection gap is informational.

It must NOT automatically block or rank investment opportunities.

---

## 40. Unknown Protection Need

If:

```text
required_life_coverage = None
```

then:

```text
protection_gap = None
```

Optionally include:

```text
PROTECTION_NEED_UNKNOWN
```

Do not treat unknown as zero.

---

# Partial Financial Data

## 41. Financial State Status

Support logically equivalent:

```text
READY
PARTIAL
POLICY_NOT_READY
UNSUPPORTED
```

Missing facts should affect only decisions requiring them.

Example:

```text
monthly expenses unknown
```

must not prevent existing rights from passing through.

But a new-cash investment requiring liquidity assessment must not receive `ALLOW`.

Use:

```text
FINANCIAL_INPUT_REQUIRED
```

---

# Reason Codes

## 42. Required Reason Codes

At minimum:

```text
EXISTING_RIGHT_PASSTHROUGH

FINANCIAL_INPUT_REQUIRED

EMERGENCY_FUND_BELOW_FLOOR
EMERGENCY_FUND_PRESERVED
ZERO_ESSENTIAL_EXPENSE_BASE

CRITICAL_DEBT_PRESENT

LIQUIDITY_COMMITMENT_CONFLICT
ALLOCATION_CAPPED_BY_LIQUIDITY
NO_SPENDABLE_SURPLUS

PROTECTION_GAP
PROTECTION_NEED_UNKNOWN

UPSTREAM_NOT_AVAILABLE
GUARDRAIL_POLICY_NOT_READY
```

Important business meaning must not exist only in prose.

---

# Precedence

## 43. Guardrail Precedence

New-cash decision precedence must be deterministic:

```text
1. Upstream discovery availability
2. Financial policy readiness
3. Required financial input completeness
4. Critical high-cost debt
5. Emergency-fund floor
6. Mandatory liquidity commitments
7. Allocation ceiling / CAP
8. Protection informational warnings
9. ALLOW
```

Document and test this order.

---

# No Opaque Score

## 44. Forbidden Scoring

Do NOT create:

```text
financial_safety_score
weighted_guardrail_score
risk_score
0–100 score
```

Guardrail output must remain explainable:

```text
CAP
because:
- protected emergency reserve
- mandatory tuition commitment
```

not:

```text
score = 0.62
```

---

# Contracts

## 45. FinancialState Contract

Logically equivalent output:

```json
{
  "status": "READY",
  "liquid_assets": "500000.00",
  "monthly_essential_expenses": "50000.00",

  "emergency_fund_months": "10.00",
  "emergency_reserve_floor": "150000.00",
  "emergency_reserve_target": "300000.00",

  "near_term_committed_cash": "100000.00",
  "protected_liquidity": "250000.00",
  "spendable_surplus": "250000.00",

  "critical_debt_balance": "0.00",
  "critical_debt_ids": [],

  "protection_gap": null,

  "policy_id": "...",
  "policy_version": "...",
  "state_hash": "..."
}
```

---

## 46. GuardrailResult Contract

Logically equivalent:

```json
{
  "status": "READY",

  "discovery_hash": "...",
  "financial_state_hash": "...",

  "planning_date": "2026-09-21",
  "available_budget": "100000.00",

  "assessments": [
    {
      "opportunity_id": "TH-OPP-THAI-ESG-2026",
      "decision": "ALLOW",
      "max_feasible_allocation": "100000.00",
      "reason_codes": []
    }
  ],

  "policy_version": "...",
  "engine_version": "...",
  "guardrail_hash": "..."
}
```

---

## 47. No Recommendation Semantics

Forbidden semantic fields:

```text
recommended
recommended_amount
rank
score
best
optimal
winner
priority
```

Allowed:

```text
max_feasible_allocation
```

because it is a safety ceiling, not advice.

---

## 48. Ordering

Guardrail assessments must preserve Discovery ordering.

Do NOT reorder by:

```text
tax saving
capacity
decision
APR
amount
```

This is not recommendation ranking.

---

# Determinism / Audit

## 49. Engine Version

Introduce:

```text
GUARDRAIL_ENGINE_VERSION
```

Initial:

```text
tax-gps-guardrails/0.1.0
```

---

## 50. Financial State Hash

Material hash must include every input affecting state:

```text
FinancialProfile
Financial Policy version/hash
planning_date
```

Use canonical serialization + SHA-256 consistent with existing Tax GPS architecture.

---

## 51. Guardrail Hash

Material guardrail hash must bind at minimum:

```text
profile hash
discovery hash
financial state hash
policy hash
planning date
available budget
guardrail engine version
guardrail output
```

---

## 52. GuardrailSnapshot

Create immutable replayable snapshot containing at minimum:

```text
profile_hash
discovery_hash
financial_state_hash

financial_policy_id
financial_policy_version
financial_policy_hash

planning_date
available_budget

guardrail_engine_version

guardrail_output
guardrail_hash
```

---

## 53. Replay

Identical material inputs must reproduce identical:

```text
FinancialState
FinancialState hash
GuardrailResult
Guardrail hash
```

Changing any material input must invalidate replay, including:

```text
liquid assets
expenses
debt APR
debt balance
cash commitment
protection data
available budget
planning date
financial policy
discovery result
engine version
```

---

## 54. No Hidden Clock

Material logic must not call:

```text
date.today()
datetime.now()
```

All date-dependent behavior uses explicit `planning_date`.

---

## 55. AI Boundary

AI MUST NOT:

```text
calculate emergency reserves
classify debt
determine guardrail decisions
calculate allocation ceiling
fill missing financial inputs
estimate protection needs
override BLOCK/CAP/REQUIRE_REVIEW
```

Guardrails must work identically with AI completely disabled.

---

# Mandatory Acceptance Tests

## 56. Financial-State Tests

### FIN-01 — Emergency fund

Input:

```text
liquid assets = 300,000
essential expenses = 50,000
```

Expected:

```text
emergency fund months = 6
floor = 150,000
target = 300,000
```

### FIN-02 — Protected liquidity

```text
liquid assets = 300,000
expenses = 50,000
mandatory near-term cash = 100,000
```

Expected:

```text
floor = 150,000
protected liquidity = 250,000
spendable surplus = 50,000
```

### FIN-03 — No negative surplus

```text
liquid assets = 100,000
protected liquidity = 200,000
```

Expected:

```text
spendable surplus = 0
```

### FIN-04 — Critical debt

```text
APR = 18%
balance = 100,000
```

Expected:

```text
critical debt balance = 100,000
```

### FIN-05 — Below threshold

```text
APR = 10%
```

must not be classified as critical under the 15% policy.

Do not label it safe/good.

---

## 57. Guardrail Tests

### GR-01 — Existing right passthrough

Even with:

```text
critical debt
emergency fund < 1 month
```

parent allowance remains:

```text
ALLOW
```

### GR-02 — Critical debt blocks Thai ESG

```text
Thai ESG = AVAILABLE
critical debt APR = 18%
```

Expected:

```text
BLOCK
max_feasible_allocation = 0
CRITICAL_DEBT_PRESENT
```

### GR-03 — Low emergency fund blocks Thai ESG

```text
liquid assets = 100,000
expenses = 50,000
```

Expected:

```text
2 months emergency coverage
Thai ESG = BLOCK
```

### GR-04 — Liquidity cap

```text
liquid assets = 200,000
expenses = 50,000
budget = 100,000
```

Expected:

```text
emergency floor = 150,000
spendable surplus = 50,000

Thai ESG:
CAP
max_feasible_allocation = 50,000
```

### GR-05 — Healthy state

```text
liquid assets = 500,000
expenses = 50,000
no critical debt
no commitments
budget = 100,000
Thai ESG capacity >= 100,000
```

Expected:

```text
ALLOW
max_feasible_allocation = 100,000
```

### GR-06 — Commitment reduces feasibility

```text
liquid assets = 300,000
expenses = 50,000
mandatory cash need = 100,000
budget = 100,000
```

Expected:

```text
CAP
max_feasible_allocation = 50,000
```

### GR-07 — Critical debt + intrinsic purpose

Using test-ready Solar:

```text
solar intent = true
critical debt exists
```

Expected:

```text
REQUIRE_REVIEW
```

### GR-08 — Emergency shortfall + intrinsic purpose

Test-ready Solar:

```text
intent = true
emergency fund < floor
```

Expected:

```text
REQUIRE_REVIEW
```

### GR-09 — Upstream unavailable

Production Solar currently:

```text
RULE_NOT_READY
```

Expected guardrail:

```text
NOT_APPLICABLE
UPSTREAM_NOT_AVAILABLE
```

### GR-10 — Missing expenses

```text
monthly expenses = None
```

Thai ESG must not receive an `ALLOW`.

Expected:

```text
FINANCIAL_INPUT_REQUIRED
```

### GR-11 — Budget > liquid assets

Must fail validation / fail closed.

### GR-12 — Protection gap

```text
required cover = 3,000,000
existing cover = 1,000,000
```

Expected:

```text
protection_gap = 2,000,000
PROTECTION_GAP
```

No automatic investment block solely from this fact.

### GR-13 — Protection unknown

```text
required coverage = None
```

Expected:

```text
protection_gap = null
```

not zero.

### GR-14 — Determinism

Identical inputs:

```text
identical FinancialState
identical GuardrailResult
identical hashes
```

### GR-15 — Replay mutation

Changing any material financial/policy/context/discovery input must reject replay.

### GR-16 — No recommendation leakage

No material output/model fields containing:

```text
recommended
rank
score
best
optimal
winner
```

---

# Golden Persona Extensions

## 58. G01 — First Jobber / Zero Tax

If financially healthy:

```text
Thai ESG guardrail may ALLOW
```

while Discovery remains:

```text
current tax benefit = 0
```

Do not turn ALLOW into recommendation.

---

## 59. G03 — High Income / Healthy Cash

With adequate liquidity and no critical debt:

```text
Thai ESG may remain ALLOW
```

within:

```text
budget
tax capacity
financial feasibility
```

---

## 60. G05 — High-Cost Debt

Use generic fixture:

```text
APR = 18%
```

Expected:

```text
Thai ESG = BLOCK
CRITICAL_DEBT_PRESENT
```

Do not assert that all Thai credit cards charge exactly 18%.

---

## 61. G06 — Emergency Fund 1 Month

Expected:

```text
Thai ESG = BLOCK
EMERGENCY_FUND_BELOW_FLOOR
```

---

## 62. G07 — Protection Gap

When explicit protection requirement exists and coverage is insufficient:

```text
PROTECTION_GAP
```

must appear.

No specific insurance product recommendation.

---

# Engineering / Quality

## 63. Regression

All accepted existing tests must continue passing.

Baseline:

```text
384 tests
```

Final suite should normally be:

```text
> 384 tests
```

Do not delete meaningful tests merely to preserve counts.

---

## 64. Coverage

Maintain:

```text
100% statements
100% branches
```

Do not use meaningless coverage padding.

Negative tests should assert behavior, not merely execute branches.

---

## 65. CI

Must continue to pass on:

```text
Python 3.12.x
```

with the existing runtime assertion.

Required gates:

```text
ruff check
ruff format --check
mypy --strict
pytest + branch coverage
uv build
```

---

# Git / Review Workflow

## 66. Workflow

Use:

```text
merged main
    ↓
feature/tgps-p1-003-financial-guardrails
    ↓
implementation
    ↓
local verification
    ↓
push
    ↓
PR
    ↓
GitHub CI
    ↓
Implementation Report
    ↓
Independent GPT Review
    ↓
merge only after acceptance
```

Do not merge before independent acceptance.

---

## 67. Requirement File

Before substantive implementation, persist this specification as:

```text
docs/requirements/TGPS-P1-003.md
```

This file is the canonical implementation requirement for the phase.

Do not materially reinterpret the requirement from chat memory.

If implementation discovers a genuine ambiguity that materially affects behavior:

```text
STOP
```

and document it rather than inventing product policy.

---

# Implementation Report

## 68. Required Report

Create:

```text
docs/implementation-reports/TGPS-P1-003.md
```

Include:

```text
A. Implementation summary
B. Architecture/modules
C. Financial Profile model
D. Financial State formulas
E. Financial Policy and provenance
F. Explicit statement: PRODUCT POLICY — NOT LAW
G. Guardrail precedence
H. Guardrail matrix
I. Reason codes
J. Determinism / audit / replay
K. Tests and marker counts
L. Statement / branch coverage
M. CI evidence
N. Python runtime
O. Requirement coverage mapping
P. Deviations
Q. Assumptions
R. Open issues
S. BPMN / DMN impact
T. Git branch / commits / PR
```

---

## 69. Expected Guardrail Matrix

Document at least:

| Condition             | INVESTMENT_TAX | Intrinsic-purpose new cash        |
| --------------------- | -------------- | ---------------------------------- |
| Critical debt         | BLOCK          | REQUIRE_REVIEW                    |
| Emergency below floor | BLOCK          | REQUIRE_REVIEW                    |
| No spendable surplus  | BLOCK          | REQUIRE_REVIEW                    |
| Partial liquidity     | CAP            | CAP where mechanically applicable |
| Healthy / sufficient  | ALLOW          | ALLOW                              |

Upstream unavailable opportunities remain `NOT_APPLICABLE` regardless of this table.

---

# BPMN / DMN

## 70. BPMN Impact

Conceptual flow becomes:

```text
Tax State
    ↓
Existing Rights / Opportunity Discovery
    ↓
Financial State Assessment
    ↓
Financial Guardrail Evaluation
    ↓
Feasible Opportunity Set
```

No optimizer yet.

---

## 71. DMN Alignment

Keep explicit deterministic decision boundaries for:

```text
Emergency Fund Status
Critical Debt Classification
Liquidity Capacity
Guardrail Decision
```

Do not introduce a generic business-rules DSL.

Typed code + versioned policy remains preferred.

---

# Accepted P1-002 Technical Debt

## 72. Existing Follow-up Items

Preserve but do not automatically remediate:

```text
F-01 — positional opportunity rule resolution
F-02 — TaxRule / OpportunityRule period-validation asymmetry
F-03 — hard-coded trusted-host allowlist
```

They are not prerequisites for `P1-003`.

Only touch them if `P1-003` directly requires a change for correctness.

If so, document the dependency and add regression tests.

---

# Definition of Done

## 73. Completion Criteria

`TGPS-P1-003` is complete only when:

```text
FinancialProfile implemented
FinancialState deterministic

Emergency reserve modeled
Debt APR modeled
Critical debt classified
Committed liquidity modeled
Protection gap modeled without inference

Financial Guardrail Policy versioned
Financial policy fail-closed

Existing rights pass through
Critical-debt guardrail works
Emergency-floor guardrail works
Liquidity CAP works
Intrinsic-purpose REQUIRE_REVIEW works
Partial financial inputs fail safely

No ranking or recommendation introduced

Financial-state hashing implemented
Guardrail hashing implemented
Audit snapshot implemented
Replay implemented

All old tests pass
All new tests pass
100% statement coverage
100% branch coverage
Python 3.12 CI passes
Build passes

Implementation report completed
Independent review passes
```

---

# Stop Condition

## 74. STOP After P1-003

After implementation, verification, push, PR and report:

```text
STOP
```

Do NOT begin:

```text
Candidate Generator
Outcome Engine
Pareto Optimizer
Recommendation Engine
Projection Engine
Fund selection
Insurance recommendation
```

Wait for independent acceptance review.

---

# Next Intended Phase

After `TGPS-P1-003` acceptance, the next intended milestone is:

```text
TGPS-P1-004 — Candidate Allocation & Outcome Engine
```

That phase will begin combining:

```text
available budget
+
legal tax capacity
+
financial feasibility ceilings
```

into feasible candidate allocations.

Only after candidate generation/outcome calculation should Tax GPS introduce Pareto optimization and plan postures such as:

```text
Tax Max
Balanced
Liquidity First
Goal First
```
