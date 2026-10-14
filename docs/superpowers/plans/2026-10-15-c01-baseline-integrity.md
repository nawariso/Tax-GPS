# C01 Baseline Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement TGPS-C01 without publishing incomplete tax baselines.

**Architecture:** Add a pure readiness decision before salary calculation. Preserve reasons and missing facts through immutable tax/discovery output and the adapter. Version evidence bundles separately and explicitly select historical artifacts for replay.

**Tech Stack:** Python standard library, Decimal/Money, pytest/ruff/mypy, existing local HTTP/JS demo.

**Spec:** `docs/requirements/TGPS-C01-baseline-integrity.md` version 0.1, approved for execution by the user's subsequent “โอเครครับ ลุย!”.

## สถานะความคืบหน้า (อัปเดต 2026-10-15)

สัญลักษณ์: `- [x]` เสร็จพร้อมหลักฐาน · `- [ ]` ยังไม่เสร็จ · **🟡 บางส่วน** = เริ่มแล้วแต่ยังไม่ครบ ·
`↳ ทำแล้ว:` บอกว่าทำอะไร/อย่างไร · หลักฐานละเอียดอยู่ใน ledger
`docs/implementation-reports/TGPS-C01-progress.md`

**วิธีตรวจ frontend:** ใช้ `uv run --locked python -m examples.check_web_demo` (เปิด server ใหม่บน port ว่าง)
ห้ามรัน `node tests/web/test_app.cjs` ตรงๆ เพราะจะยิงไปที่ server ที่ค้างอยู่บน 8765 ซึ่งอาจเป็นโค้ดเก่า

| Task | สถานะ |
| --- | --- |
| 1 Core readiness | ✅ เสร็จ (Python 673 passed); lint/format/mypy ค้างไป Task 5 |
| 2 Consumers/UI | ✅ เสร็จ (Python 683 passed, frontend 23/23); ข้อจำกัดที่ทราบอยู่ใน ledger |
| 3 Versioned evidence | 🟡 บางส่วน — evidence, 1.0.1 resources, loader selectors มีแล้ว |
| 4 HTTP diagnosis | 🟡 บางส่วน — มีโค้ด `Connection: close` + `_discard_rejected_body` และ test แล้ว; ยังขาดหลักฐาน diagnosis (จำนวนรอบ/เวลา) |
| 5 Verification/report | ⬜ ยังไม่เริ่ม |

## Global Constraints

- Section 40(1), 2026; preserve existing progressive PIT and financial guardrails.
- Status precedence ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY.
- Missing inputs are not zero. Positive retirement/prior usage remain unsupported until C02.
- Keep previous artifacts byte-for-byte; current engine must reject historical snapshots.
- No network/clock/AI in calculation; runtime dependencies remain standard library only.
- Core coverage 100% statements/branches; local runtime recorded separately from Python 3.12 CI.
- Work in current authorized checkout on `feature/tgps-c01-baseline-integrity`; preserve pre-existing Stage 4 draft.
- Execute inline; user has authorized implementation. Use a fresh final reviewer as required by executing-plans.

## Review Focus

1. Forged non-READY state with a numeric taxable base cannot call tax_impact (Task 1).
2. Unknown pool names cannot bypass positive-usage restrictions, including zero-value unknown groups (Task 1: validation error).
3. Legacy seven-field requests and extended profile requests fail consistently; reasons contain no raw financial data (Task 2).
4. Old result selections/downloads cannot return after an error or late response (Task 2).
5. Catalog rotation does not allow historical catalog/policy to become current allocation authority (Task 3).

## File map and interfaces

- `src/tax_gps/calculation/readiness.py`: `assess_baseline(profile: UserProfile) -> BaselineReadiness` with status, codes and missing facts.
- `calculation/models.py`: TaxStatus.REQUIRES_INPUT; TaxState material reason_codes/missing_fact_ids/calculation_scope; guarded tax_impact.
- `engine.py`: readiness gate; core version 0.2.0; no retirement deduction or positive retirement rights.
- `discovery/models.py`, `discovery/engine.py`: propagate baseline readiness evidence, version 0.3.0.
- `examples/demo_profile.py`, `examples/web_demo.py`, `examples/web/*.js/html`: structured input errors and no stale tax output.
- `policy/loader.py`, `opportunity/loader.py`: current version selection and explicit old-version loading.
- Existing pack/catalog JSON retained; new versioned JSON and evidence notes added.
- Tests: add `tests/acceptance/test_baseline_integrity.py`, extend real-engine API/browser tests, provenance/version tests; migrate only fixtures whose C01 meaning changed.
- Ledger: `docs/implementation-reports/TGPS-C01-progress.md` (native Windows bookkeeping instead of POSIX shell helpers).

## Task 1: Core readiness and evidence

Consumes UserProfile and ActivatedRulePack; produces TaxState with machine reasons and declared coverage.

- [x] Write tests: default unknown shared usage → REQUIRES_INPUT/null PIT; explicit () → READY/79,000; positive retirement/known-pool usage → UNSUPPORTED; unknown parent → REQUIRES_INPUT; combined reasons follow specified order; unknown pool raises InvalidValueError; forged non-READY tax_impact raises. AC01–08/12/14.
  ↳ ทำแล้ว: `tests/acceptance/test_baseline_integrity.py` (14 cases)
- [x] Run `uv run --locked pytest tests/acceptance/test_baseline_integrity.py -q`; inspect expected missing-readiness failures.
  ↳ ทำแล้ว: RED 13 failed / 1 passed ตามคาด (ยังไม่มี readiness)
- [x] Implement the pure readiness decision and immutable output fields; gate before allowances; remove unreachable positive-retirement baseline treatment while retaining public capacity functions.
  ↳ ทำแล้ว: `calculation/readiness.py` ใหม่; gate ใน `engine.py`; reason/missing fields ใน `calculation/models.py`; discovery เทียบทั้ง replayed hash และผลจริง (กันยอด PIT เก่าที่ hash ไม่เปลี่ยน). GREEN 14 passed
- [x] Update existing fixtures to explicit known-zero usage only when their intended profile has no prior purchases; change positive/unknown fixtures to new expected non-READY contracts. Preserve independent golden expectations.
  ↳ ทำแล้ว: ใส่ explicit zero เฉพาะ fixture salary/artwork/solar ที่รู้ครบ; positive usage/retirement เปลี่ยนเป็น blocked baseline โดยคงสูตร capacity เดิม
- [x] Run full Python suite; ledger RED/GREEN and any contract migration.
  ↳ ทำแล้ว: เจอ 224 failed จาก test helper `tests/support/catalog.py` (json.dumps กับ mappingproxy) → แก้ให้อ่าน raw JSON 1.0.1 → 673 passed. ruff/format/mypy ยังมีค้าง (ดู ledger) เลื่อนไป Task 5

## Task 2: Consumers and presentation

Consumes Task 1 TaxState; produces DiscoveryResult carrying baseline codes/missing facts and HTTP error JSON with `code`, `status`, `reason_codes`, `missing_fact_ids`.

- [x] Add failing tests for downstream evidence, rejected candidate activation/build, legacy/extended positive/unknown requests, unknown eligibility, actual HTTP error envelope and browser stale-output lifecycle. AC09–11/17/18.
  ↳ ทำแล้ว: Python `test_web_demo.py` 3 tests (structured errors, HTTP envelope, rejected POST); Node 2 cases C01 (lifecycle)
  ↳ ทำแล้ว (รอบนี้): `test_demo_profile.py` 7 cases extended profile ตรวจ code/status/reason/missing และไม่เผยยอดเงิน (AC09/AC11);
    `test_candidate_capacity_authority.py` 2 cases `build_candidates` ปฏิเสธ tax non-READY แม้ได้ policy ที่เคยถูกต้อง (AC09);
    `test_web_demo.py` ข้อความ READY ต้องบอกขอบเขตและรายการที่ยังไม่รวม. AC17/18: guardrail/family fixtures เดิมผ่าน
  ↳ แก้บันทึกเดิม: ที่เคยเขียนว่า Node 2 cases RED เพราะได้ 200 เป็นความเข้าใจผิด — ตอนนั้นยิงไป server เก่าที่ค้างบน 8765; กับ server ใหม่ผ่าน 23/23 อยู่แล้ว
- [x] Run targeted Python and Node tests; inspect genuine contract failures.
  ↳ ทำแล้ว: RED จริงที่ยืนยันได้ = assertion ใหม่ (ข้อความ error เฉพาะรายการ, แสดง missing ids, ข้อความ READY) — fail กับโค้ดเดิม, ผ่านหลังแก้
- [x] Propagate discovery evidence, add a structured ValueError subtype for domain/input readiness, and adapt parser/HTTP/JS without exposing raw profile values. Domain remains authority for retirement/prior-usage checks.
  ↳ ทำแล้ว: `DiscoveryResult` มี baseline_status/reason_codes/missing_fact_ids; `examples/demo_errors.py` `DemoInputError`;
    unknown `retirement_usage`/`other_income` มี reason `RETIREMENT_INPUT_REQUIRED`/`OTHER_INCOME_INPUT_REQUIRED` (เดิมไม่มี reason)
- [x] Replace UI claims of all existing rights being included with scoped language; preserve explicit unknowns and invalidate result/export/selection on errors.
  ↳ ทำแล้ว: `index.html` ใช้ “รวมรายการที่รองรับและกรอกยืนยันแล้ว · 40(1) ปี 2569” + “ยังไม่รวม: เงินออมเกษียณ (PVD/RMF), Thai ESG/ESGX เดิม, รายได้อื่น”;
    `app.js` error ที่เป็น BASELINE_NOT_READY/INPUT_REQUIRED แสดงข้อความเฉพาะรายการ + ข้อมูลที่ยังขาด แทนคำแนะนำกลางเรื่องจำนวนเงิน
- [x] Run full Python and frontend suites; ledger evidence.
  ↳ ทำแล้ว: Python 683 passed; frontend (check_web_demo) 23/23

## Task 3: Versioned evidence and historical selection

Consumes governed bundle schema; produces current pack/catalog versions 1.0.1 and explicit `version="1.0.0"` historical loads. Production allocation still binds only to current bundled catalog.

- [ ] **🟡 บางส่วน** Add failing tests for current source evidence, immutable historical load, invalid version/hash selectors, replay mismatch and historical catalog rejection by production candidate activation. AC13–15.
  ↳ ทำแล้ว: `tests/acceptance/test_c01_artifact_versions.py` 5 tests (ผ่าน). ยังต้องยืนยัน: production candidate activation ปฏิเสธ historical catalog
- [ ] Run targeted provenance/version tests and inspect failures.
- [x] Retrieve authoritative full text; record page/section, source URL, dates and content hash in evidence notes. Use SEC Q&A for 2026 pool. Resolve SSO direct legal text; if unresolved, report and fail closed as the spec requires.
  ↳ ทำแล้ว: `docs/policy-evidence/2026-10-15/README.md` — SSO จากราชกิจจาฯ (เก็บ PDF + SHA-256), SEC Q&A หน้า 1–2. ข้อจำกัด: ดาวน์โหลด PDF ของ SEC ไม่ได้ จึงไม่มี checksum ของไฟล์ต้นฉบับ
- [ ] **🟡 บางส่วน** Add new versioned resources; keep original resource bytes. Loader accepts explicit supported versions (optional expected hash) and rejects unknown selectors. Update current fixture loaders and candidate/catalog policy identities consistently; bump consumer versions where material output changes.
  ↳ ทำแล้ว: pack/catalog `@1.0.1` (ไฟล์ 1.0.0 เดิมไม่แตะ); loader รับ `version`/`expected_hash` และปฏิเสธ version อื่น. ยังต้องตรวจ: identity ของ consumer และ version bump
- [ ] Retain matching historical engine artifacts/reproduction instructions and reject old snapshots under current versions. Run replay/version and full suites; ledger evidence.

## Task 4: HTTP failure diagnosis

Consumes existing DemoHandler; produces a documented, tested diagnosis of F09.

- [ ] Inspect reject-before-body-read lifecycle; attempt targeted repetitions and full-suite reproduction with actual Windows sockets. Record counts and runtimes.
- [ ] If a code defect is established, add a failing narrow regression before changing response/connection handling; otherwise record evidence and OPEN/conditional status.
- [ ] Preserve Host/Origin/framing/size/private-file boundaries; run all HTTP and frontend tests. AC16.

## Task 5: Verification, migration and report

- [ ] Run locked lint, format, strict mypy, full branch coverage, real-engine frontend lifecycle and build. Inspect every result; add meaningful missing-branch cases only.
- [ ] Write C01 implementation report with AC01–18 mapping, migration/version notes, legal evidence and F09 diagnosis; update README, demo contracts, roadmap and decisions from actual results.
- [ ] Obtain one fresh final code review of implementation, tests, spec and ledger. Fix important findings with RED→GREEN and full verification; record any remaining limitation.
- [ ] Verify final diff/status; keep implementation evidence distinct from independent milestone acceptance and remote CI.

## Pre-flight self-review

Task 2 consumes precisely Task 1 reason_codes/missing_fact_ids. Task 3 changes default artifacts consumed by every fixture and Task 2; rotate fixture loaders atomically and re-run all consumers. Task 4 owns HTTP connection lifecycle and must preserve Task 2's structured envelopes. Shared interface conflicts resolved against the C01 spec.

No automatic push/merge/publish. Commit only task-owned work if repository permissions allow; exclude pre-existing unrelated files.
