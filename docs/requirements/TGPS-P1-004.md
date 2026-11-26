# TGPS-P1-004 — Candidate Allocation & Outcome Engine

Project: Tax GPS (`nawariso/Tax-GPS`)
Canonical base: `92bc65b7e5140807f86a0caecfbebb5f6cc8fb54` (`origin/main`)
Implementation branch: `feature/tgps-p1-004-candidate-allocation-outcome`
Status: implementation candidate; independent acceptance pending.

## Purpose and boundary

Given accepted TaxState, DiscoveryResult, FinancialState, GuardrailResult, a budget carried by the guardrail result, and explicit applicable allocation/tax policy, enumerate feasible allocation compositions and their exact tax and financial outcomes. This phase neither ranks nor recommends them. No winner, utility, score, Pareto frontier, objective function, market-data call, expected return, projection, Monte Carlo simulation, or P1-005 decision belongs here.

## Inputs and integrity

Use the existing typed immutable tax/discovery/financial/guardrail objects. Reject incompatible years, hashes, policy/catalog identities, financial readiness, duplicated opportunity/assessment identities, invalid financial state hashes and malformed ceilings. Unknown financial values remain unknown. `ALLOW` and `CAP` only permit new-cash opportunities explicitly AVAILABLE with a known remaining capacity and nonnegative ceiling not exceeding the available budget or known surplus. `BLOCK`, `REQUIRE_REVIEW` and `NOT_APPLICABLE` must not generate new cash. Existing rights are already reflected in TaxState, never allocated again.

`AllocationPolicy` is raw input, not authority. Production `build_candidates` accepts only `ActivatedAllocationPolicy`, freshly validated against the exact bundled, EFFECTIVE P1-002 opportunity catalog, the policy ID/version/tax year/status, and the accepted UserProfile, DiscoveryResult and TaxState identities. A self-consistent DiscoveryResult hash is integrity metadata, not independent authority for remaining tax capacity. Activation requires `profile.profile_hash() == discovery.profile_hash`, deterministically replays `discover_opportunities(profile, tax, tax._activated_pack, catalog, DiscoveryContext(tax.tax_year, discovery.planning_date))`, compares both the replay hash and material content, and independently asserts each allocatable capacity using P1-002 `calculate_opportunity_capacity` with the governed cap and assessable-income rate, `TaxState.income.assessable_income`, and `profile.opportunity_facts.shared_limit_amount_used`. Unknown shared usage must remain unknown and may not become an allocatable opportunity. Only after these checks may the shared remainder populate the bundled policy; a rehashed or edited DiscoveryResult cannot authorize it. Activation derives the only supported `FULL_ALLOCATION_DEDUCTION` treatment from AVAILABLE governed opportunities and verifies `TaxState.tax_impact(remaining_capacity).saving == maximum_tax_saving_at_capacity` before publishing any outcome. The activated evidence retains profile/catalog/policy/discovery/tax hashes, rule_ids, and source_ids; candidate snapshots retain hashes, not raw profile facts. No arbitrary caller-provided treatment, unsupported percentage, unknown opportunity, extraneous group, or unbound policy hash can grant tax authority. Non-1:1 allocation-to-deduction semantics are deferred until a separately authorized upstream policy/catalog change. Shared remaining capacity equals the replayed discovered capacity for the sole currently governed member of a group; the production activation path fails closed on a generalized multi-opportunity shared group, rather than inventing a shared-capacity rule. Synthetic multi-opportunity tests call only a private construction helper and cannot activate production authority. Artwork and solar remain inactive in the accepted catalog.

## Candidate construction and output

Always produce NO_ACTION first: empty allocations, zero incremental cash, unchanged PIT, unchanged spendable surplus and protection gap. Generate only the zero boundary and intersections of per-opportunity guardrail/tax ceiling, aggregate budget, remaining spendable surplus and shared group remainder, plus residuals that fund another opportunity at its own governed ceiling. No search increments are invented. Sort opportunity IDs and canonical allocation JSON; deduplicate by composition, not construction path. Candidate ID is SHA-256 of canonical allocation content alone. All emitted amounts are positive Money, sorted by opportunity ID; candidate output is baseline first and then canonical allocation bytes. The explicit policy maximum is at most 256 and no more than eight positive allocatable
opportunities enter expansion; exceeding either bound fails before publishing results.
Overflow raises before returning any candidate, never truncates a partial set.

For each candidate use `TaxState.tax_impact(deductible_amount)`, which calls the progressive tax core; verify its before-tax result matches the accepted TaxState. `tax_saved = tax_before - tax_after`. Cash outflow is allocation, not tax saved; unused budget is original budget minus allocated cash. Post-candidate spendable surplus is the P1-003 surplus less allocated cash, never credited with hypothetical tax refunds. Protection gap is propagated unchanged when no governed protection-effect metadata exists. Each immutable outcome includes allocation content and hashes for tax rule pack, guardrail, input identities, policy and engine version. Stable reasons describe baseline, binding budget, CAP, shared limit, full deduction and partial financial state. A frozen snapshot and replay compare hashes and the entire canonical output.

## Acceptance matrix

- Baseline: NO_ACTION for zero budget, blocked opportunities and partial liquidity, tax unchanged.
- Boundaries: whole-satang budget below/at/above target, exact CAP and zero surplus; no amount over budget or liquidity.
- Policy: ALLOW/CAP, blocked/new-cash ineligibility, explicit full deduction only; unactivated, malformed, unsupported, unknown, or missing policy fails closed. Recompute P1-002 maximum tax saving before activation; reject self-consistently hashed semantic disagreements.
- Shared: production activation binds the sole accepted group member to replayed P1-002 capacity and rejects unknown or inconsistent remainders. Verify the governed cap and income rate against accepted profile shared usage, including non-zero and unknown usage; self-rehashed discoveries must not increase capacity. Synthetic construction tests prove combined group allocation never exceeds one group remainder; generalized multi-member activation is not authorized.
- Tax: progressive PIT across brackets, zero tax benefit, deductible amount above taxable base floors taxable income at zero.
- Financial: liquidity safety and unknowns preserved; known protection gap propagated without actuarial estimates.
- Determinism: canonical input and policy ordering, stable SHA-256 IDs, no duplicate composition, multiple executions and serialized snapshot replay.
- Bounded: policy maximum and engine hard maximum of 256; overflow fails closed.
- Golden: employee, two opportunities, budget-bound, shared collision, CAP, NO_ACTION-only, tax saving despite reduced spendable surplus, and zero additional benefit. Assert exact Money outcomes and reason codes.

Quality gates: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy --strict`, `uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q` (100% statement and branch), `uv build`. Push to a feature branch and run exact-SHA CI; do not merge before independent review.

Open future scope: a separate, explicitly authorized phase may compare feasible candidates; P1-004 publishes no preference or choice.
