# Stage 3 comparison demo — review handoff

Status: implemented and locally verified for the current bundled demo; independent review
and remote CI remain open. This is presentation scope approval, not core acceptance.

Branch: `feature/demo-stage3-comparison`.
Base: `52f5bb24d360d0d1dfaf11f60ceedc10cf3fd907` (Stage 2).

The explicit authorization was: “อนุมัติ Stage 3 ตามร่าง และอนุญาตพัฒนาเดโมแยกระหว่างรอ gate เดิม”.
See the [approved presentation contract](stage3-comparison-contract-draft.md).
The original draft filename is retained; this does not create an approved P1-005 milestone.

## Artifact and scope

- `examples/web/app.js`: current-result-bound selection, pinned NO_ACTION, comparison
  rows from the authoritative candidate fields, per-opportunity holding/source details,
  guardrail explanations, invalidation, and presentation-only export metadata.
- `examples/web/index.html`: user-operated checkboxes, semantic comparison table,
  horizontal-scroll guidance, and explicit profile/export privacy warning.
- `examples/web/profile.css`: table-contained horizontal scrolling and selection controls.
- `tests/web/test_app.cjs`: real HTTP/engine-backed comparison/lifecycle regressions.

No Python adapter, pure core, policy/catalog, dependency, CI workflow, engine identity or
core canonical hash contract was changed. No optimizer, ranking, preference filter,
recommendation, market service, persistence, or purchase instruction was added.

## Selection and export contract

Every successful calculation begins with only the pinned baseline in the table. Cash
candidates are opt-in and stay in engine order, independent of click order. The selection
is scoped to the current result hash; each rendered checkbox also captures the request
generation, so an old detached control cannot reselect a candidate after recalculation
even when the unchanged inputs reproduce the same result hash.

The downloaded object preserves all existing result fields and adds `comparison_view`:

- `version`: string `1` (presentation format, not engine version).
- `kind`: `USER_SELECTED_COMPARISON`.
- `result_hash`: exactly the exported `outcomes.result_hash`.
- `selected_candidate_ids`: selected non-baseline IDs in current engine order.

NO_ACTION is implicit and pinned, not a user-selected recommendation. This object is
outside `outcomes`, does not mutate canonical engine material, and is not sent to the
backend. Editing inputs or starting another calculation clears table, selection and
export availability. No export is produced while the current result is invalid/pending.

## Verification

- TDD: the new comparison regressions first failed because the feature was absent;
  the unchanged older tests passed. A later detached-control regression reproduced
  stale reselection after same-input recalculation, then passed with generation binding.
- 21 JavaScript tests passed with real HTTP responses from the local engine; only DOM
  and response delivery timing are controlled in the harness.
- 650 Python tests passed; core statement/branch coverage remained 100%.
- Locked dependency sync, Ruff lint/format, strict mypy and source/wheel build passed.
- Actual browser exercised initial baseline, native checkbox selection/deselection,
  exact displayed fields, unchanged engine material, JSON download, recalculation,
  detached old controls, zero-tax-benefit selection, debt-only baseline and unknown liquidity.
- A browser race held two real fetch responses and released the newer one first;
  the older response did not replace the newer result or its selected table row.
- Widths 1440, 390 and 360 kept page-level overflow absent and allowed scrolling within
  the table region. Desktop/mobile screenshots were inspected. The frame intentionally
  clips offscreen columns until scrolled; this is not truncation of engine data.

Generated illustrative evidence is Git-ignored under `examples/artifacts/`:
`stage3-browser-checks.json`, `stage3-export.json`, `stage3-desktop.png`, `stage3-mobile.png`.
Do not upload real-person exports as evidence; they include submitted profile facts.

## Current catalog limitation and review scope

The bundled production demo currently exposes only one positive allocatable opportunity.
Consequently its normal result compares NO_ACTION with that one cash candidate; blocked
or unknown-liquidity results may have only NO_ACTION. This UI does not fabricate additional
opportunities to make the table richer. Multiple-cash-candidate click-order and multi-
opportunity-composition runtime acceptance remain unexercised with this bundled catalog.
The renderer iterates allocations and filters in engine order, but that source inspection
is not claimed as an actual multi-opportunity production-path test. Such cases require a
separately authorized governed catalog/engine path before that broader gate can be closed.

Self-review is same-author only, not independent acceptance. Remote CI for the exact
Stage 3 commit is UNVERIFIED; feature-branch push alone does not run the existing workflow.
P1-004 independent acceptance remains pending. No merge, tag, release, new core milestone,
or production/privacy/legal approval is implied by these local checks.

## Reproduce

Use the commands in the [demo guide](local-web-demo.md). Open the local demo, select the
checkbox under a cash candidate, and scroll the table to inspect holding/provenance columns.
The selection does not change calculated amounts. Clear the checkbox or edit any profile
input to verify the corresponding table/export reset behavior.
