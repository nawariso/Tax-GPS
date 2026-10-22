# UI01 Fintech Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox (`- [ ]`) syntax for tracking. One fresh final reviewer; no per-task implementer agents.

**Goal:** Restyle the existing local Tax GPS calculator after the approved cream/forest fintech reference.

**Architecture:** Keep current IDs, native form/disclosure behavior and engine-driven rendering. Replace only the presentation shell and styles. Use native fragment links to existing salary/scenario controls, CSS circuit decoration, and no additional assets/dependencies.

**Tech Stack:** Local HTML/CSS, existing plain JS and standard-library Python HTTP demo.

**Spec:** `docs/requirements/TGPS-UI01-fintech-restyle.md` v0.1, approved by user “โอเครครับ ลุย!” after the full proposal.

## Global Constraints

- Preserve existing C01 uncommitted work and unrelated Stage 4 draft; work in the current authorized feature checkout.
- No tax core, policy/catalog, readiness, guardrail, selection/export behavior or runtime dependency changes.
- All new visible copy is Thai; no invented marketing metrics, auth, trial, sync or recommendation.
- Retain hidden-state enforcement and existing form element IDs/names, safe errors and keyboard focus.
- Native fragment CTAs target `salary` and `scenario`; no navigation JS required.
- Keep all resources local; pointer-inert decorations; responsive at 1440/390/360px, internal table scrolling.
- Ledger: `docs/implementation-reports/TGPS-UI01-progress.md`. Native Windows bookkeeping replaces POSIX helpers as in C01.

## Review Focus

1. Non-READY/error states must not leak visible tax text through new hero/decorations.
2. The two CTAs must resolve to visible focusable existing controls; CSS scroll margins must keep targets clear.
3. Thai long error/scope copy and large money values must wrap on 360px without page overflow.
4. New forest/gold visual emphasis must not imply ranking or recommendation between cash candidates.
5. Header/hero must not bury the working calculator or remove existing scenarios, unknown options, disclosures or audit controls.

## Task 1: Presentation shell and dashboard styling (AC01–07)

Files: `examples/web/index.html`, `examples/web/style.css`, `examples/web/profile.css`.
Test: `tests/acceptance/test_web_demo.py`; existing JS lifecycle stays authoritative.
Consumes: existing `app.js` / `profile.js` IDs and dynamic classes. Produces: same contract plus two native anchor links; no new JS interface.

- [x] Finish baseline sync/Python/frontend, inspect Git; copy current UI files to ignored tmp before editing.
  ↳ ทำแล้ว: baseline 694 Python / frontend 24/24; Git HEAD80afe5a บน feature เดิม, backup current HTML/CSS/JS ที่ tmp/ui01-before โดยไม่ stash/reset
- [x] RED: real HTTP page parser verifies two primary fragment links and that each resolves to an existing text input/select (`#salary`, `#scenario`) without JS, not a placeholder. Run targeted test; expect missing links.
  ↳ ทำแล้ว: 1 failed / 35 deselected เพราะ links ยังไม่มี; ไม่สร้าง test ที่ตรวจ CSS strings
- [x] Implement centered Thai hero, local/year pill, native CTAs, inert circuit/orbit decoration and a compact workspace section heading. Retain scope notices and all existing IDs/form content.
  ↳ ทำแล้ว: index.html เพิ่ม hero/native fragment links/skip link/workspace intro/CSS-SVG decoration; คง IDs และ form เดิม
- [x] Replace style.css with organized forest/cream design tokens, 1408px shell, responsive hero, working input/results panels, neutral peer candidate cards, table-scroll treatment, strong focus and reduced-motion handling. Restyle profile.css to match.
  ↳ ทำแล้ว: ปรับ 2 CSS โดยคง native disclosures/table scroll/hidden states; เพิ่มความเข้มและขนาดข้อความรองสำหรับภาษาไทย ไม่มี JS/assets/dependencies ใหม่
- [x] GREEN: targeted real HTTP navigation test; full Python and fresh-server frontend. Visual styling earns render review, not CSS-string tests.
  ↳ ทำแล้ว: targeted 1 passed, full 695 passed / frontend24; quality gates รอบแรกทั้งหมดผ่าน (695 / 100% coverage). Visual QA ยัง UNVERIFIED เพราะ browser provider ว่าง
- [x] Mark exact changed files/results/methods in ledger and checkboxes.

## Task 2: Verification, review and interactive handoff (AC01–08)

Files: UI01 requirement/plan/ledger/report, roadmap, decisions, demo guide/README pointers as needed.
Consumes: Task 1 unchanged IDs/native links. Produces: exact gate results, honest visual evidence/limitations, fresh local demo.

- [x] Inspect current browser-provider availability. If usable, review desktop/mobile screenshots and keyboard CTA behavior; otherwise record visual gate UNVERIFIED and leave user preview as the review point, never invent screenshots.
  ↳ ทำแล้ว: cua.getState apps=[] / browsers=[]; ไม่ใช้เครื่องมืออื่นควบคุม UI แทนและไม่อ้าง screenshot QA; ต้องให้ผู้ใช้ดู preview จริง
- [x] Run all seven locked quality gates per tgps-verify; record real runtime separately from Python 3.12 CI.
- [x] Dispatch one fresh read-only reviewer for the UI01 delta (pre-edit copies available under tmp/ui01-before), spec, ledger and review focus. Fix Important/Critical findings with actual RED→GREEN; record minors/rulings.
- [x] Update report/checkboxes/requirement/roadmap/append-only DEC with actual status; retain unverified gates explicitly rather than marking acceptance.
- [x] Start a new loopback server on an OS-selected port, smoke-check current page/API, open browser for the user. Preserve other servers/processes and all working changes; no push/merge.

## Preflight and execution ruling

Task 2 consumes Task 1's unchanged IDs and HTML-only fragment actions; no conflicting shared interface. The user approved the concrete design and asked to proceed; no second plan-approval question is needed for these implementation details. Execute inline under the established native workflow, preserving the current checkout. No new worktree or commit is required to make the reversible result reviewable.

## Progress

| Task | Status |
| --- | --- |
| 1 Presentation | DONE — RED→GREEN, Python695 / frontend24; visual QA แยกเป็น UNVERIFIED |
| 2 Verify/review/preview | DONE — final gates/source review ผ่าน, preview64946 smoke9/9; visual acceptance UNVERIFIED |


## จุดรับช่วง — 2026-10-15

- [x] Task 1–2 implementation/automatic verification/source review/handoff ทำแล้ว
  ↳ final locked gates: sync/lint/format/mypy clean, Python695 passed in11.06s / coverage100% (2846 statements,798 branches), frontend24/24, build0.2.0; smoke9/9 ตรวจ current asset bytes และ API จริง
  ↳ fresh reviewer ui01_final_review ไม่พบ Critical/Important/Minor ที่ยืนยันจาก source; รายงาน TGPS-UI01-review.md
  ↳ วิธีทำ: native fragment links แทน navigation JS; local CSS/inline SVG แทน template/framework/asset imports; Windows inline+ledger แทน POSIX helpers. JS เดิม byte-identical, IDs46เดิมอยู่ครบ
  ↳ preview ใหม่ http://127.0.0.1:64946/ PID35652; metadata tmp/ui01-play-session.json เป็นข้อมูลเฉพาะ session ต้องตรวจ server ก่อนใช้ในครั้งถัดไป
- [ ] Visual acceptance: ภาพที่1440/390/360, Thai clipping/overflow, real keyboard focus/scroll และเทียบ reference ยัง UNVERIFIED เพราะ CUA apps/browsers=[]; อย่าอ้าง automatic tests ว่าตรวจสิ่งเหล่านี้แล้ว
- ไม่ต้องทำ restyle/TDD/gates เดิมซ้ำหาก code ไม่เปลี่ยน; รับช่วงที่ visual review ของ preview และ feedback ผู้ใช้ ไม่เปลี่ยน C01/C02 tax scope หรือถือว่า ACCEPTED

## Rendered review follow-up — 2026-10-20

- [x] Chrome1440/390/360 screenshots, Thai/default/error copy, keyboard skip/CTA
  focus/disclosure and internal table scroll checked; approximate reference compared.
- [x] UI01-AC05 decorative-dot overflow fixed: rendered RED390=375/385,
  360=345/355 → GREEN375/375,345/345; desktop1425/1425. Single CSS inset change,
  no document overflow hiding, no new CI test; evidence is real rendered geometry.
- [x] Full seven locked gates passed: Python695/11.61s,100%coverage2846/798,
  frontend24/24, lint/format148/mypy102/build clean; fresh source review0findings.
- [ ] **PARTIAL:** rendered reduced-motion mode NOT RUN; user visual acceptance pending.
  Task2 follow-up report: [rendered review](../../implementation-reports/TGPS-UI01-visual-review-2026-10-20.md).
  Earlier UNVERIFIED notes describe the original session. No milestone acceptance,
  C01 F09 closure, C02 treatment, commit/push/merge is implied by this follow-up.
