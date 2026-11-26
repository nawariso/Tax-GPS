# Tax GPS — Next Milestones Plan

> For Hermes: execute only after explicit authorization, using the currently active model. Do not delegate across models or bypass independent acceptance.

## Goal

พาจาก local demo ที่คำนวณได้ ไปสู่ผลิตภัณฑ์ที่ทดลองกับโปรไฟล์จริงในขอบเขตที่รองรับได้ โดยรักษาความถูกต้องของ policy และแยกการทดสอบออกจาก production approval

## Planning snapshot (historical; not current Git state)

- Local branch: `feature/tgps-p1-004-candidate-allocation-outcome`.
- Local HEAD: `49339a1` (R2 remediation). Remote PR/CI status was not reverified in this planning turn.
- Historical accepted milestone: P1-003. P1-004 canonical requirement and implementation report still label independent acceptance pending.
- Local demo changes are uncommitted: `.gitignore`, `README.md`, `pyproject.toml`, `examples/`, `docs/demo/`, `tests/acceptance/test_web_demo.py`.
- The preceding execution verified 625 tests, core statement/branch coverage 100%, lint, format, strict types, build and browser interactions. Those counts are historical execution evidence, not a fresh test run for this planning turn.
- `docs/requirements/TGPS-P1-004.md:38` requires independent review before merge.
- `docs/requirements/TGPS-P1-004.md:40` allows future candidate comparison only under a separately authorized phase.
- No canonical P1-005 requirement was found in `docs/requirements/`. Future phase titles and scope below are proposals, not an approved original roadmap.

## Architecture

Keep the deterministic, framework-free core authoritative. UI and future API adapters pass explicit validated inputs through existing activation and calculation functions; they must not duplicate tax formulas, silently convert unknowns to zero, or promote feasibility into recommendation. Treat production deployment and legal-policy freshness as separate acceptance gates.

## Technology

Existing Python/uv core and standard-library local demo; no new framework or persistence technology is selected in this plan.

## Stage 1 — Close the current reviewable work

### Task 1: Review the pending demo diff

Files: `examples/web_demo.py`, `examples/web/index.html`, `examples/web/app.js`, `examples/web/style.css`, `tests/acceptance/test_web_demo.py`, `docs/demo/local-web-demo.md`, `README.md`, `pyproject.toml`, `.gitignore`.

Read actual files and compare with live Git state. Check scope/assumptions, privacy claims, unknown-input handling, stale output on errors and responsiveness. Keep generated financial exports and screenshots under the ignored `examples/artifacts/` directory.

### Task 2: Repeat quality gates

Run from repository root:

```console
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv build
```

Repeat browser checks for the four scenarios, editable budget, invalid input/recovery, rights view and JSON export. Test rapid successive scenario changes for stale-response races before calling the adapter review-ready. Report actual counts and distinguish core coverage from adapter/UI coverage.

### Task 3: Publish only when explicitly authorized

Preserve existing implementation/R1/R2 commits. Choose whether the separately authorized demo belongs in a separate review artifact or as a distinct commit on the current branch; do not silently mix domain acceptance with UI approval. Commit/push only after authorization, verify exact remote SHA and exact-SHA CI, then request independent P1-004 R2 review. Merge only after acceptance. No reset, amend or squash of reviewed history without explicit permission.

Deliverable: accepted core baseline plus a clearly reviewed demo checkpoint, or an honest list of outstanding gates.

## Stage 2 — Complete input and explanation for the already-supported domain

This stage requires explicit UI scope approval; it is not an automatic expansion of P1-004.

### Task 4: Agree an input-to-domain matrix

Inspect `src/tax_gps/profile/models.py` and `src/tax_gps/financial/profile.py` again. Map existing supported fields to UI: eligible parent/child facts, mortgage-interest facts, retirement contributions, debts, mandatory committed cash and known/unknown protection coverage. Record legal eligibility evidence requirements rather than inventing automatic eligibility. Decide which fields remain unsupported in the first usable version.

Proposed artifact after approval: `docs/demo/input-coverage.md`.

### Task 5: Extend the adapter one supported field group at a time

Likely changes: `examples/web_demo.py`, `examples/web/index.html`, `examples/web/app.js`, `examples/web/style.css`, `tests/acceptance/test_web_demo.py`, `docs/demo/local-web-demo.md`.

For each group: write failing acceptance tests, verify RED, implement only the approved mapping, verify GREEN and rerun the full suite. Use public existing value objects and engines. Do not add new tax law or new income categories through the UI.

### Task 6: Make explanations usable

Show missing facts, unsupported profiles, binding financial ceilings and existing rights already included in baseline. Separate PIT liability from any future withholding/refund reconciliation. Link result evidence to governed rule/source metadata without suggesting that hashes prove legal freshness.

Deliverable: an end-to-end employee planning journey with fewer hidden assumptions, not merely attractive demo cards.

## Stage 3 — Authorize candidate comparison / decision support

Possible next identifier: P1-005, subject to the user's canonical requirement. Do not create or implement that requirement as approved policy in this turn.

### Task 7: Settle the decision contract before writing an optimizer

Define whose preferences determine a comparison: liquidity floor, lockup tolerance, intrinsic need, protection priorities and cost. Decide whether output is a user-controlled comparison or a governed recommendation, how ties work, how unknowns fail closed, and how NO_ACTION remains visible. Do not equate maximum tax saving with the best outcome.

### Task 8: Implement only the accepted contract

Create new source/test paths only after the canonical requirement defines them. Reuse `src/tax_gps/candidate/models.py` and accepted candidate output as evidence, not as permission to invent scores. Use RED/GREEN tests with exact expected outcomes, deterministic replay and policy identities. Separate review and acceptance from passing tests.

Deliverable: an explainable comparison or decision-support layer with approved semantics. Fund selection, market forecasts and AI advice remain out of scope unless separately authorized.

## Stage 4 — Productize after the domain gates

### Task 9: Choose deployment and privacy boundaries

Agree whether the first release is single-user local or hosted. Only then choose API/UI framework, authentication, persistence, retention/deletion, transport security and operational monitoring. The standard-library loopback HTTP server is not a production hosting plan.

### Task 10: Production readiness and real-use acceptance

Verify each activated material rule's current authoritative provenance before real-use approval; keep partially verified rules inactive. Test the complete workflow with consented data inside the supported domain, with no unsupported-income approximations. Define who grants legal/domain acceptance and who grants runtime/product acceptance. Publish a rollback and policy-version strategy before a release.

Deliverable: a scoped usable release with explicit limitations and evidence, not a claim that the demo is ready for all taxpayers.

## Recommended immediate order

Close Stage 1 first. After that, prioritize Stage 2's complete input/explanation flow over AI, product recommendations or adding more decorative screens. Draft Stage 3 only once its canonical requirement and objective are supplied/approved.

## Risks and open decisions

- P1-004 independent acceptance is still an open prerequisite; a demo request does not grant it.
- The demo currently assumes personal eligibility and no debts/commitments/family deductions; do not use it outside that scope.
- Current law was not reverified by building the demo.
- Broader inputs may uncover unsupported domain combinations; report them rather than silently approximating.
- Scores, utility weights and ranking rules are product policy and must be explicitly governed.
- No commit/push, merge, dependency installation, API deployment or project-code change is authorized by this planning-only turn.
