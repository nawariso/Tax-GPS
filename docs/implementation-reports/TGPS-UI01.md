# TGPS-UI01 — Fintech restyle implementation report

Date: 2026-10-15. Requirement v0.1 approved by user “โอเครครับ ลุย!”.
Status: **IMPLEMENTED** — automatic gates/source review complete; visual acceptance pending.
Independent acceptance: NOT ACCEPTED. Rendered desktop/mobile visual QA: UNVERIFIED.

2026-10-20 update: rendered1440/390/360 and keyboard checks now have
[real screenshots and measurements](TGPS-UI01-visual-review-2026-10-20.md).
Fixed one decorative-dot overflow; all local gates pass. Reduced-motion mode and
user acceptance remain pending. UNVERIFIED statements below describe the original
2026-10-15 report, not the newer checks.

## Changes

- `examples/web/index.html`: centered Thai hero, dark forest/cream identity, real
  native fragment actions to salary/scenario, keyboard skip link, local compass SVG
  with circuit/orbit decoration, workspace/year introduction. Retains all existing
  input/result IDs and scope disclosures. Shared-usage hint now describes existing
  C01 blocking accurately; no readiness logic changed.
- `examples/web/style.css`: structured cream/forest design tokens, frame/header,
  larger hero, restrained green CTAs/gold decoration, neutral peer candidate cards,
  responsive calculator panels, focus/reduced-motion and hidden-state rules.
- `examples/web/profile.css`: profile records/breakdowns/comparison match the new
  appearance; internal wide-table scrolling retained.
- `tests/acceptance/test_web_demo.py`: live HTTP parser test verifies two real hero
  links resolve to visible input/select targets. RED1 → GREEN1. No CSS-string tests.

No JS, Python adapter/core, policy/catalog or dependency edits belong to UI01.
Prior C01 working changes remain preserved. HEAD80afe5a plus uncommitted working tree;
no commit/push/merge claimed. Pre-edit UI copies in ignored tmp/ui01-before distinguish
UI01 from the already-uncommitted C01 delta.

## Evidence and limits

Baseline: locked sync, Python694 / frontend24. Post-change full suite695 and frontend24
passed. First seven quality gates passed with 100% core statement/branch coverage.
Final gate/reviewer records follow below; earlier first-gate results are history.

| AC | Evidence / status |
| --- | --- |
| AC01 reference appearance | Cream/forest/centered hero/circuit intent implemented; rendered comparison UNVERIFIED |
| AC02 working actions | Real HTTP fragment/target parser RED→GREEN; actual browser focus/scroll UNVERIFIED |
| AC03 authoritative values | Existing real engine/API/lifecycle regressions retained; no hero tax figures added |
| AC04 blocked/stale outputs | Existing 24 real-engine frontend lifecycle cases pass; hidden-state CSS retained |
| AC05 desktop/mobile | Responsive source rules implemented; screenshots/overflow at 1440/390/360 UNVERIFIED |
| AC06 keyboard/reduced motion | Native links + visible focus + reduced-motion source rules; real keyboard/render review UNVERIFIED |
| AC07 local/privacy | Local CSS/inline SVG and existing server assets only; no external font/CDN/storage/network services introduced |
| AC08 tracking/gates | DONE: plan/ledger/report/DEC updated, final source review/gates passed, preview smoke9/9 |

The reference was inspected as its public preview image, not imported template source.
No reference brand/customer/trial/auth claims were copied. The site uses existing local
HTML/CSS rather than a React/Tailwind template import; local CSS/SVG creates decoration.
The native Windows inline ledger replaces POSIX SDD tooling as in the previous task.

Visual tooling limitation: cua.getState returned apps=[] / browsers=[]; no desktop,
mobile screenshots or real-browser focus/overflow checks are claimed. Automated lifecycle
uses a simulated DOM with real HTTP/engine responses and cannot prove CSS rendering.
The user receives a fresh live preview for visual review. This limitation prevents
calling all UI acceptance cases passed even if automatic gates are green.

Core C01 F09 remains OPEN / conditional; UI work does not resolve that intermittent
transport cause, expand tax coverage or grant C01/P1-004 acceptance. Remote CI/Python3.12
verification is not claimed; local runtime is recorded in final gate evidence.


## Final verification and review

All seven locked CI-equivalent gates passed after the final typography/color refinement:
sync/lint/format (144files)/strict mypy(102files), Python **695 passed in11.06s** with
**100% statements/branches** (2846/798, zero misses), fresh-server frontend24/24 and
sdist/wheel0.2.0 build. Local CPython3.14.3 / Windows11; no remote CI3.12 claim.
[Raw evidence](TGPS-UI01-verification.json) includes actual commands/outputs, source
hashes, ID/asset audit, sampled contrast and fresh interactive smoke checks.

Fresh reviewer ui01_final_review found no confirmed Critical/Important/Minor source
issues. [Review record](TGPS-UI01-review.md) preserves its declined visual judgments.
All46 prior IDs remain; current48 are unique. app.js/profile.js are byte-identical to
pre-UI01 copies and all four external-to-document asset URLs remain local. Calculated
solid-color samples are evidence only, not a full rendered accessibility certification.

Preview: **http://127.0.0.1:64946/** (server PID35652), started on an OS-selected unused
loopback port, with no existing process stopped. Smoke9/9 confirms current HTML/CSS/JS
bytes plus real supported/unknown/prior/invalid API responses. Browser tools unavailable,
so user receives a clickable link; no browser-open or screenshot QA is claimed.

Implementation and handoff are done. Next work is rendered desktop/mobile/keyboard
review and user feedback; keep AC01 rendered portion, AC05 and AC06 rendered portion
UNVERIFIED until real evidence is available. Do not reimplement this restyle simply
because visual acceptance remains pending. There are no deferred minor source findings.
