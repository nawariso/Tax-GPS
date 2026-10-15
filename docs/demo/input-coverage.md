# Stage 2 demo input contract

Authorization: the user explicitly permits Stage 2 as a separate demo while core review
and CI remain pending. This exception permits development only, not milestone acceptance,
merge, release, legal-policy certification, or production use.

Base: `d15d840c4ee3f1ae50321ffb948a9f5f2be75c9a`; branch `feature/demo-stage2-profile`.
The original Stage 2 authorization kept core/artifacts unchanged. The separately authorized
C01 requirement now governs baseline readiness and artifact 1.0.1; this contract is updated
to describe that current behavior without retroactively changing Stage 2 acceptance.

## Input-to-domain mapping

| Screen input | Existing authoritative model | Adapter behavior |
| --- | --- | --- |
| Salary / social security | IncomeProfile / ExistingTaxBenefits | Existing validated amounts; Section 40(1) only |
| Personal eligibility | ExistingTaxBenefits.personal_eligible | Explicit yes/no; unknown blocks publishing a tax result |
| Parent records | Parent(relationship, eligible) | Explicit identity and confirmed eligibility; unknown blocks, duplicate identity rejected by core |
| Child records | Child fields: child_id, order, legally_eligible, birth_year | Explicit legal order, Gregorian birth year, identity and eligibility; no eligibility inference |
| Mortgage interest / eligibility | ExistingTaxBenefits.mortgage_interest_paid / mortgage_eligible | Actual interest, not loan payments; unknown eligibility blocks |
| Assets / essential expenses | FinancialProfile | Blank remains None; numeric zero stays known zero |
| Debt records | Debt | ID, category, outstanding balance, APR percentage, minimum monthly payment, secured yes/no; APR is converted exactly to a ratio, with no invented 100% upper bound |
| Committed payments | CommittedCashNeed | ID, amount, due date, mandatory flag and description; existing engine alone decides near-term reserve inclusion |
| Needed / existing life cover | ProtectionProfile | Blank remains unknown; both known values permit the core gap calculation; no automatic insurance need estimate |
| Thai ESG shared usage | SharedLimitUsage | Known zero/complete empty list permits supported baseline; positive → domain UNSUPPORTED; blank/None → REQUIRES_INPUT; no PIT/savings/candidates/export for either blocked state |
| Other income | IncomeProfile.unsupported | Positive or unknown value blocks the salary-only demo, not silently ignored |
| Retirement contributions | ExistingTaxBenefits.retirement_contributions | Positive value → domain UNSUPPORTED; unknown → parser REQUIRES_INPUT; known zero permits supported salary baseline. Standalone capacity math does not deduct contributions from PIT taxable income |

Empty record lists explicitly mean no such records for this experiment. The screen must
say this; users who have not checked whether their lists are complete must not treat an
empty list as verified real-world data. Legacy seven-field requests remain supported only
under their explicitly stated narrower assumptions, never as a full-profile request.

## API boundary

An extended request is the original seven string fields plus `profile`, containing exactly
these keys: `personal_eligible`, `parents`, `children`, `mortgage_interest`,
`mortgage_eligible`, `debts`, `commitments`, `required_coverage`, `existing_coverage`,
`other_income`, `retirement_usage`.

Scalar values and record fields are strings. Boolean strings are `true` / `false`;
`unknown` is rejected where the core cannot preserve it in a published tax result.
Amounts are nonnegative THB with at most two decimals. APR percentage accepts at most
four decimal places and is converted with the core exact decimal context. Record keys
are checked exactly, malformed types and duplicate identities fail closed. Dates and
integer syntax are validated, not repaired. The existing HTTP body cap of 4096 bytes
remains a technical local-demo limit, not a tax rule.

## Explanation contract

Return the core tax-state breakdown, financial state, guardrail decisions and normalized
submitted profile with output hashes. Show emergency reserves, near-term commitments,
critical debt, missing protection facts and family/mortgage allowances separately.
Do not label a remaining capacity as an amount to spend or an ALLOW decision as advice.
Debt minimum payment and secured status are captured facts, not an extra reserve formula:
users should include recurring essential payments in monthly expenses without double counting.

Eligibility selections are caller assertions, not legal verification. The application does
not infer legal eligibility from age, birth order, relationship or payment receipts and
does not collect identity documents. Current legal freshness is not established by this UI.
No ranking, persistence, external services, automatic recommendation or filing is added.


## C01 error identity (2026-10-15)

Malformed values use structured INVALID_INPUT with a code-owned field path; unknown
booleans use canonical scalar or indexed record paths, e.g. children[1].legally_eligible,
debts[1].secured, commitments[1].mandatory (zero-based indices). Standard parent role IDs
remain parent.father.eligible / parent.mother.eligible; caller-defined relationship text
is replaced by parent[index].eligible in errors. Submitted financial values and arbitrary
record labels are not copied into error text/IDs. Constructor errors retain safe row or
profile scope. These are adapter/evidence fixes; domain readiness and deduction scope
are unchanged. Final automated frontend lifecycle: 24/24; Python suite: 694 tests.
