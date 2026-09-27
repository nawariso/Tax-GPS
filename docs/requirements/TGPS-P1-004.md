# TGPS-P1-004 — Candidate Allocation & Outcome Engine

Project: Tax GPS (`nawariso/Tax-GPS`)
Canonical base: `92bc65b7e5140807f86a0caecfbebb5f6cc8fb54` (`origin/main`)
Implementation branch: `feature/tgps-p1-004-candidate-allocation-outcome`
Status: implementation candidate; independent acceptance pending.

## Purpose and boundary

Given accepted TaxState, DiscoveryResult, FinancialState, GuardrailResult, a budget carried by the guardrail result, and explicit applicable allocation/tax policy, enumerate feasible allocation compositions and their exact tax and financial outcomes. This phase neither ranks nor recommends them. No winner, utility, score, Pareto frontier, objective function, market-data call, expected return, projection, Monte Carlo simulation, or P1-005 decision belongs here.

## Inputs and integrity

Use the existing typed immutable tax/discovery/financial/guardrail objects. Reject incompatible years, hashes, policy/catalog identities, financial readiness, duplicated opportunity/assessment identities, invalid financial state hashes and malformed ceilings. Unknown financial values remain unknown. `ALLOW` and `CAP` only permit new-cash opportunities explicitly AVAILABLE with a known remaining capacity and nonnegative ceiling not exceeding the available budget or known surplus. `BLOCK`, `REQUIRE_REVIEW` and `NOT_APPLICABLE` must not generate new cash. Existing rights are already reflected in TaxState, never allocated again.

`AllocationPolicy` is an explicit caller-supplied, identity-bearing policy input; no deduction semantics is inferred from an allocation. Every allocatable opportunity must have a named `OpportunityTreatment`: `FULL_ALLOCATION_DEDUCTION` or an explicit `PERCENTAGE_OF_ALLOCATION` with a governed Percentage rate. A shared group must have a separately declared remaining limit, computed upstream from accepted usage and the governing product/tax policy; never treat the single-opportunity remaining capacities as independent shared pools. Its policy ID, catalog hash, treatment entries, group remainders and bound are hashed into every result. The engine checks consistency of the supplied policy hash and discovery catalog identity; the caller remains responsible for supplying accepted, authoritative treatment and group-usage evidence. The bundled catalog leaves artwork and solar inactive; synthetic multi-opportunity fixtures do not activate those rules for production.

## Candidate construction and output

Always produce NO_ACTION first: empty allocations, zero incremental cash, unchanged PIT, unchanged spendable surplus and protection gap. Generate only the zero boundary and intersections of per-opportunity guardrail/tax ceiling, aggregate budget, remaining spendable surplus and shared group remainder, plus residuals that fund another opportunity at its own governed ceiling. No search increments are invented. Sort opportunity IDs and canonical allocation JSON; deduplicate by composition, not construction path. Candidate ID is SHA-256 of canonical allocation content alone. All emitted amounts are positive Money, sorted by opportunity ID; candidate output is baseline first and then canonical allocation bytes. The explicit policy maximum is at most 256 and no more than eight positive allocatable
opportunities enter expansion; exceeding either bound fails before publishing results.
Overflow raises before returning any candidate, never truncates a partial set.

For each candidate use `TaxState.tax_impact(deductible_amount)`, which calls the progressive tax core; verify its before-tax result matches the accepted TaxState. `tax_saved = tax_before - tax_after`. Cash outflow is allocation, not tax saved; unused budget is original budget minus allocated cash. Post-candidate spendable surplus is the P1-003 surplus less allocated cash, never credited with hypothetical tax refunds. Protection gap is propagated unchanged when no governed protection-effect metadata exists. Each immutable outcome includes allocation content and hashes for tax rule pack, guardrail, input identities, policy and engine version. Stable reasons describe baseline, binding budget, CAP, shared limit, full deduction and partial financial state. A frozen snapshot and replay compare hashes and the entire canonical output.

## Acceptance matrix

- Baseline: NO_ACTION for zero budget, blocked opportunities and partial liquidity, tax unchanged.
- Boundaries: whole-satang budget below/at/above target, exact CAP and zero surplus; no amount over budget or liquidity.
- Policy: ALLOW/CAP, blocked/new-cash ineligibility, explicit full and partial deduction; malformed or missing policy fails closed.
- Shared: combined group allocation cannot exceed one group remainder, including collisions across opportunities.
- Tax: progressive PIT across brackets, zero tax benefit, deductible amount above taxable base floors taxable income at zero.
- Financial: liquidity safety and unknowns preserved; known protection gap propagated without actuarial estimates.
- Determinism: canonical input and policy ordering, stable SHA-256 IDs, no duplicate composition, multiple executions and serialized snapshot replay.
- Bounded: policy maximum and engine hard maximum of 256; overflow fails closed.
- Golden: employee, two opportunities, budget-bound, shared collision, CAP, NO_ACTION-only, tax saving despite reduced spendable surplus, and zero additional benefit. Assert exact Money outcomes and reason codes.

Quality gates: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy --strict`, `uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q` (100% statement and branch), `uv build`. Push to a feature branch and run exact-SHA CI; do not merge before independent review.

Open future scope: a separate, explicitly authorized phase may compare feasible candidates; P1-004 publishes no preference or choice.
