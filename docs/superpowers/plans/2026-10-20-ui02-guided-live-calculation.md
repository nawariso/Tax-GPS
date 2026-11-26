# UI02 Guided Live Calculation Implementation Plan

> Use superpowers:executing-plans inline; one fresh final reviewer. No implementer agents.

**Goal:** Thai guided inputs, automatic calculation, stable output space and restrained motion.
**Architecture:** Preserve server/domain and all existing IDs. Keep pending/error skeleton outside the authoritative result; debounce the same API with calculationVersion guarding publication. CSS animates only validated destination values.
**Tech stack:** Existing HTML/CSS/JS, Python standard library.
**Spec:** docs/requirements/TGPS-UI02-guided-live-calculation.md, approved 2026-10-20 “โอเครครับ ลุย!”

## Constraints and review focus

- No core, packs/catalog, readiness, unknown semantics, storage or dependency changes.
- 450ms debounce; manual submit/scenario immediate; stale results/export/selection never usable.
- Keep pending structure and dimensions, never stale financial text. Respect reduced motion.
- Tests: rapid edits, late responses, duplicate input/change, add/remove dynamic records, invalid fields, optional unknowns, hidden disclosure errors and focus; rendered 1440/390/360 and reduced motion.
- Existing dirty feature checkout and scoped backups retained; no commit/push/merge. Plan mechanics execute under user's approved implementation instruction; no repeat approval.

## Task 1 — Lifecycle (AC03–07)

Files: examples/web/app.js, profile.js; tests/web/test_app.cjs.
Interface: invalidateResults() clears authoritative state and schedules; calculate(manual=false) cancels timer, checks native validity without unsolicited popup and guards response version.
- [x] RED: deterministic fake timers; UI02 tests rapid edits, immediate submit, stale hidden output, response race and errors, change deduplication, record mutations.
- [x] Implement debounce and persistent placeholder shell; never display stale values, cancel animation by hiding old result. Readable status/error links.
- [x] GREEN: fresh-server lifecycle and Python suite; ledger RED/GREEN and changed test contract.

## Task 2 — Guided presentation and delivery (AC01–02,07–09)

Files: index.html, style.css, profile.js hints/disclosures, docs tracking.
Consumes Task1 skeleton IDs liveShell/liveStatus/inputStatus; produces three guided groups with labels/hints and local motion.
- [x] Reorganize native disclosures, mark essential facts visible; preserve all field IDs/names/default semantics. Add helper copy and per-group counts.
- [ ] **PARTIAL:** Rendered keyboard/focus, large numbers, errors, unknowns and mobile overflow checked. Reduced-motion source checked; runtime reduce-mode remains unverified (no browser media override).
- [x] Run seven locked gates. Fresh reviewer compares backup-to-current UI02 delta; fix important findings with RED→GREEN.
- [x] Update requirement/plan/ledger/roadmap/README/append-only DEC; provide fresh loopback preview. IMPLEMENTED is not ACCEPTED.

## Progress

Task1 DONE; Task2 implementation/gates/review/delivery DONE; reduced-motion runtime check and user acceptance pending.
Baseline: Python695 and frontend24 passed in current conversation.
Self-review: Task2 consumes Task1 IDs defined above; all spec sections map to tasks; no domain contract extension.

↳ ทำแล้ว: RED32=25pass/7fail; GREEN32; actual HTML schema RED33=32pass/1fail→GREEN33; review RED37=33pass/4fail→GREEN37. Final Python695/coverage100%, frontend37, lint/format152/mypy102/build/diffcheckผ่าน. วิธี: existing feature checkout + scoped backups, native disclosures/local CSS; current API unchanged.

## Follow-up — 2026-10-21

- [x] Reduced-motion runtime check completed using native Chrome DevTools reduce emulation on a fresh loopback server; active Styles disables animation/transition and smooth scrolling, automatic edit/recalculation and restored default verified. Media override cleared afterwards.
  ↳ Evidence: [follow-up report](../../implementation-reports/TGPS-UI02-follow-up-2026-10-21.md). The earlier PARTIAL entry is historical; runtime gap now closed for current UI02 source.
- [x] Local locked gates rerun: Python695/coverage100%, frontend37/37, lint/format153/mypy102/build clean; source hashes unchanged.
- [ ] User visual acceptance. Task2 implementation and technical checks DONE; milestone remains IMPLEMENTED, not ACCEPTED.
