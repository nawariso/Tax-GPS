# C04A Thai ESG Year-End What-If Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task after plan approval. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ผู้ใช้ใส่จำนวนเงินที่จะซื้อ Thai ESG ภายในปี 2569 บนประมาณการ C03 แล้วเห็น PIT และยอดชำระเพิ่ม/คืน ก่อนและหลัง พร้อมวงเงินสิทธิและผลตรวจเงินสำรอง

**Architecture:** บริการ domain ใหม่รับ `AnnualEstimateInput` + `AnnualEstimateResult` ของ C03 ที่ READY, จำนวนทดลอง และ `FinancialProfile` (ยอดซื้อ Thai ESG เดิมและวันที่วางแผนมาจาก C03 ไม่รับซ้ำ) วงเงินมาจาก `calculate_opportunity_capacity` เดิมด้วย catalog ที่ activate แล้ว เงินสำรองมาจาก `compute_financial_state` + `assess_new_cash_opportunity` เดิม และ PIT หลังซื้อมาจาก `calculate_tax_saving` เดิม ไม่มีสูตรภาษีหรือ guardrail ชุดที่สอง เส้นทางเดโมเดิม, `TaxState.tax_impact` และ candidate engine คง contract เดิม

**Tech Stack:** Python standard library, frozen dataclasses, `Money`/`Decimal`, pytest/Ruff/mypy, เดโม local HTTP + HTML/CSS/JS เดิม

**Spec:** [C04A v0.1](../../requirements/TGPS-C04A-thai-esg-year-end-what-if.md), [DEC-037](../../DECISIONS.md#dec-037--open-c04a-thai-esg-year-end-what-if-requirement-review), [DEC-038](../../DECISIONS.md#dec-038--c04a-review-decisions-d1d4-agreed), [หลักฐาน E1](../../policy-evidence/2026-11-26/README.md), [ตัวอย่างอ้างอิง](../../implementation-reports/TGPS-C04A-acceptance-reference.md)

**สถานะแผน:** `APPROVED` / Native ตาม [DEC-039](../../DECISIONS.md#dec-039--c04a-d5d7-agreed-plan-approved-and-native-implementation-started) · D5 (ก), D6 (ข), D7 (ก) · implementation `IN_PROGRESS`

## ข้อกำหนดร่วม

- ใช้ pack `TH-PIT-2026-001@1.2.0` และ catalog `TH-OPPORTUNITY-2026-001@1.2.0` เดิม ไม่ออก version ใหม่ใน v0.1 (D6 ข)
- ลำดับสถานะของส่วนทดลอง: C03 ไม่ READY → `UNSUPPORTED` → `REQUIRES_INPUT` → ข้อจำกัด (เกินวงเงิน / guardrail) → `READY` แยก `None` จากศูนย์ทุกช่อง
- ฐาน 30% ใช้ `tax.income.assessable_income` เหมือน discovery/candidate กรณี PVD บวกค่านี้หลังหักส่วนยกเว้น PVD ซึ่งเป็นการตีความใหม่ที่ยังไม่มีหลักฐาน จึงต้องผ่าน D7 ก่อน (ข้อเสนอ: ใช้ฐานนี้และแสดงว่าเป็นวงเงินแบบระมัดระวัง) ~~(PVD บวกจึงใช้เงินได้หลังส่วนยกเว้น PVD)~~
- ยอดซื้อ Thai ESG/ESGX เดิมเป็น fact ของ C03 อยู่แล้ว (`shared_limit_usage`, `other_rights.thai_esg/thai_esgx`) C03 ที่ READY จึงหมายถึงยอดเดิมเป็นศูนย์ ห้ามรับ input ซ้ำ
- เมื่อจำนวนเกินทั้งวงเงินสิทธิและเพดาน guardrail ให้สถานะ `EXCEEDS_TAX_CAPACITY` ก่อน (ตรวจวงเงินสิทธิก่อน guardrail) และแสดงทั้งสองค่า
- PVD บวก (`PVD_BASELINE_ONLY`) เปิดได้ตาม D1; RMF บวก (`RMF_BASELINE_ONLY`) เป็น `UNSUPPORTED` ใน v0.1; ห้ามคำนวณวงเงินเกษียณที่เหลือ
- ข้อความไทย ไม่ชี้นำ ไม่จัดอันดับ ไม่ใส่ค่าที่กรอกใน error; deterministic, standard library, loopback, ไม่มี storage/log ยอดเงิน
- Coverage 100% statements/branches และ 7 gates ตาม AGENTS §4

## จุดตรวจเพิ่มเติม

1. จำนวน 0 ต้องให้ทุกตัวเลขเท่ากับ C03 (Task 1)
2. เกินวงเงิน 0.01 ไม่คำนวณ; เท่าวงเงินคำนวณได้ (Task 1)
3. แก้ยอดคาดจนวงเงิน 30% ข้ามเพดาน 300,000 ต้องคำนวณวงเงินใหม่ (Task 1, 3)
4. `available_budget` ของ guardrail = จำนวนทดลอง ผล `CAP` ที่ต่ำกว่าจำนวนทำให้ส่วนทดลองไม่คำนวณ (D4) และแสดง `max_feasible_allocation` (Task 1)
5. Response ค้างหลังแก้จำนวนหรือยอด C03 ต้องไม่เผยผล (Task 3)

## สถานะความคืบหน้า

| Task | งาน | สถานะ |
| --- | --- | --- |
| 1 | Domain what-if (AC01–05, 07–09) | เสร็จ · 25 tests (14 functions) · Python 907 · coverage 100% |
| 1B | ปรับข้อความช่องสิทธิ LTF ใน C03 (D5) | เสร็จ · frontend 59/59 |
| 2 | Snapshot, export, replay (AC10) | เสร็จ · 20 tests · Python 927 · coverage 100% |
| 3 | HTTP และเดโมภาษาไทย (AC01–10) | เสร็จ · HTTP 16 tests · frontend 66/66 |
| 4 | ตรวจรวม, Chrome, independent review | ยังไม่เริ่ม |

## Task 1 — Domain what-if

**ไฟล์:** สร้าง `src/tax_gps/candidate/thai_esg_what_if.py`, `tests/acceptance/test_c04a_thai_esg_what_if.py` · ถ้าตัวคำนวณส่วนต่างของ C03 เป็น private ให้แยกเป็นฟังก์ชันร่วมใน `annual_estimate.py` โดยไม่เปลี่ยนผล C03

**Interfaces ที่เสนอ**

- `WhatIfStatus(StrEnum)`: `BASELINE_NOT_READY`, `UNSUPPORTED`, `REQUIRES_INPUT`, `EXCEEDS_TAX_CAPACITY`, `GUARDRAIL_LIMITED`, `READY`
- Frozen `ThaiEsgWhatIfInput(amount: Money | None, financial: FinancialProfile)`
- `evaluate_thai_esg_what_if(estimate_input: AnnualEstimateInput, estimate: AnnualEstimateResult, inputs: ThaiEsgWhatIfInput, catalog: ActivatedOpportunityCatalog, financial_policy: ActivatedFinancialPolicy) -> ThaiEsgWhatIfResult` ใช้ `estimate_input.cutoff_date` เป็น planning date และ `shared_limit_usage` ของ C03 เป็น `shared_amount_used`; ตรวจว่า `estimate` คำนวณจาก `estimate_input` นี้จริง
- Frozen `ThaiEsgWhatIfResult`: `status`, `reason_codes`, `missing_fact_ids`, `capacity: OpportunityCapacity | None`, `guardrail: GuardrailAssessment | None`, `amount`, `impact: TaxImpact | None`, `settlement_before/after` (kind + amount, `None` เมื่อยอดหักขาด), `conditions` (lock-up และ evidence จาก catalog)

**Steps**

- [x] RED: `test_c04a_amount_impact_matches_reference` (ESG-0/100K/CAP), `test_c04a_capacity_boundary` (CAP, OVER-CAP), `test_c04a_forecast_edit_moves_capacity`, `test_c04a_withholding_missing_keeps_pit`, `test_c04a_prior_usage_comes_from_c03` (1/ว่าง ทำให้ C03 ไม่ READY → `BASELINE_NOT_READY`; 0 คำนวณได้), `test_c04a_guardrail_inputs_and_limits`, `test_c04a_pvd_open_rmf_closed`, `test_c04a_blocked_baseline_hides_everything`, `test_c04a_amount_validation` (ติดลบ, เกินสตางค์ = input error ระบุช่อง)
- [x] รัน `uv run --locked pytest tests/acceptance/test_c04a_thai_esg_what_if.py -q` บันทึก RED (กรณีที่ผ่านตั้งแต่แรกบันทึกเป็น characterization)
  ↳ ทำแล้ว: RED = collection error `ModuleNotFoundError: tax_gps.candidate.thai_esg_what_if` (ทุก test ยังไม่มีโค้ดรองรับ ไม่มี characterization)
- [x] Implement: ตรวจ C03 READY และ planning availability → amount/financial ว่าง → capacity (`calculate_opportunity_capacity` กับ definition `TH-OPP-THAI-ESG-2026`, `shared_amount_used` จาก C03) → financial state + `assess_new_cash_opportunity(NewCashInputs(..., remaining_capacity=capacity.remaining, available_budget=amount, state))` → ถ้า amount > capacity หรือ > `max_feasible_allocation` ให้สถานะข้อจำกัด → `calculate_tax_saving(tax.taxable_income, amount, tax._activated_pack)` → settlement ก่อน/หลังด้วยฟังก์ชันเดียวกับ C03
- [x] GREEN targeted แล้ว `uv run --locked pytest -q`; บันทึก ledger
  ↳ ทำแล้ว: รอบแรก 20/25 ผ่าน — guardrail 4 ราย fail เพราะ `FinancialPlanningContext` ห้าม budget เกินเงินสดที่ทราบ จึงใช้ budget = min(วงเงินสิทธิ, เงินสดคงเหลือ); test ยอด 0.001 สร้าง `Money.of` ไม่ได้ จึงสร้างด้วย `Money(Decimal)` ตรง → 25/25 · full 907 passed · coverage 3,493 statements / 1,014 branches 100% · ruff/format/mypy strict (130 files) ผ่าน
  ↳ ต่างจาก interface ที่เสนอ: รับ `pack` แล้วคำนวณ C03 ภายใน (ไม่รับ `AnnualEstimateResult` จากภายนอก) เพื่อให้ผล C03 กับ input ตรงกันเสมอ; แยก `settle()` ใน `annual_estimate.py` ใช้ร่วมโดยผล C03 ไม่เปลี่ยน (test C03 เดิมผ่านครบ)

## Task 1B — ปรับข้อความช่องสิทธิ LTF (เฉพาะเมื่อผู้ใช้ตกลง D5 ก)

**ไฟล์:** `examples/web/index.html`, `tests/web/test_app.cjs`

~~เดิมเสนอเพิ่มคำถามใหม่, reason code และ bump schema ของ C03 snapshot~~ CORRECTION: C03 ถาม `fund_history.ltf_carryforward` และ `other_rights.thai_esgx` อยู่แล้ว (`calculation/readiness.py:101-112`)

- [x] RED frontend: ข้อความช่อง `fund_history_ltf_carryforward` ระบุ "รวมสิทธิยกเว้นจากการสับเปลี่ยน LTF เป็น Thai ESGX"
- [x] แก้ข้อความ ไม่เปลี่ยน id, readiness, reason code หรือ snapshot
  ↳ ทำแล้ว: RED frontend 58/59 (test ใหม่ fail) → GREEN 59/59 ผ่าน `examples.check_web_demo`; Python 907 ผ่าน ช่องนี้ใช้ร่วมกันทั้งเส้นทางเดิมและ C03 จึงเห็นข้อความใหม่ทั้งสองเส้นทาง แต่ id/readiness ไม่เปลี่ยน

## Task 2 — Snapshot, export, replay

**ไฟล์:** สร้าง `src/tax_gps/candidate/thai_esg_what_if_audit.py`, `tests/acceptance/test_c04a_thai_esg_what_if_audit.py`

- [x] RED: snapshot ผูก C03 snapshot hash, catalog content hash, financial policy hash, จำนวน, ยอดซื้อเดิม, financial profile material, ผลทั้งหมด; replay คำนวณซ้ำได้ผลเดิม; payload ที่แก้จำนวนแต่ใช้ hash เดิมถูกปฏิเสธ; สถานะไม่ READY ไม่มี snapshot
- [x] Implement ด้วย `canonical_json` + `sha256_hex`; ไม่ใช้ `json.dumps` กับ model ที่ freeze
- [x] GREEN และ full suite
  ↳ ทำแล้ว: RED collection ขาด `thai_esg_what_if_audit` → GREEN 17/17 รอบแรก แต่ coverage 99% (บรรทัดตรวจ record/array ผิดรูปแบบ) เพิ่ม malformed cases เป็น 20/20 → Python 927, coverage 3,558/1,024 = 100%; mypy รอบแรกพบ helper ใน test ไม่มี annotation แก้แล้ว; snapshot ฝัง C03 snapshot ทั้งชุด (ไม่ใช่เฉพาะ hash) เพื่อ replay ตรวจ C03 material ได้ และเพิ่ม `decode_annual_estimate_input` แบบ public ใน C03 audit

## Task 3 — HTTP และเดโมภาษาไทย

**ไฟล์:** `examples/annual_estimate_adapter.py` (block `thai_esg_what_if` ที่เป็น optional ใน request เดิม), `examples/web/annual-estimate.js`, `examples/web/index.html`, `examples/web/profile.css`, `examples/demo_errors.py`, `tests/acceptance/test_c04a_thai_esg_what_if_demo.py`, `tests/web/test_app.cjs`

- [x] RED HTTP: request ไม่มี block = response C03 เดิม byte-for-byte ในส่วน C03; block ครบ = ผลก่อน/หลังตามตัวอย่าง; ช่องผิด = error ระบุช่องโดยไม่สะท้อนค่า
- [x] RED frontend: ส่วน "ทดลองซื้อ Thai ESG" แสดงหลัง C03 READY เท่านั้น; ช่องจำนวน, ยืนยันยอดซื้อเดิมปีนี้, เงินสดคงเหลือ, ค่าใช้จ่ายจำเป็นต่อเดือน, หนี้/ภาระจ่าย (ใช้ component เดิมของเดโม); ผลคู่ก่อน/หลัง; เงื่อนไขจาก catalog; แก้ข้อมูลแล้วผลและ export เก่าหาย; response ค้างไม่เผยผล
- [x] Implement แล้วรัน `uv run --locked python -m examples.check_web_demo` (ห้ามรัน node ตรง)
  ↳ ทำแล้ว: HTTP RED 15 fail / 1 ผ่าน (ข้อที่ผ่านคือ request ไม่มี block = characterization ของ contract เดิม) → GREEN 16/16; frontend RED 7 fail → GREEN 66/66; ใช้ช่องเงินสด/ค่าใช้จ่าย/หนี้/ภาระจ่าย/ความคุ้มครองเดิมในหัวข้อ 3 (แสดงในโหมดประมาณการทั้งปี ซ่อนช่องงบทดลอง) ช่องจำนวน Thai ESG ไม่มี `name` เพื่อไม่ให้หลุดเข้า request เส้นทางเดิม; export ในโหมดทั้งปีเป็น snapshot what-if เมื่อ READY มิฉะนั้นเป็น snapshot C03 เดิม; 7 gates ผ่าน: Python 943, coverage 3,558/1,024 = 100%, frontend 66/66, ruff 216 ไฟล์, mypy 133 ไฟล์, build 0.4.0

## Task 4 — ตรวจรวมและส่งรีวิว

- [ ] `tgps-verify` ครบ 7 gates บันทึกตัวเลขจริง
- [x] Chrome 1440/390, keyboard, reduced motion บน server ใหม่พอร์ตว่าง
  ↳ ทำแล้ว: Chrome headless 158 ผ่าน CDP บน server ใหม่ (พอร์ตว่าง) ตัวเลขตรงตัวอย่างอ้างอิงทั้ง 1440 และ 390, over-cap แสดงวงเงินและไม่คำนวณ, ยอดว่างแจ้งช่องที่ขาด, overflow 0, reduced motion = animation `none`, Enter เปิดหัวข้อ 3 แล้ว Tab ถึงช่องจำนวน ([receipt](../../implementation-reports/TGPS-C04A-chrome-2026-11-27.json)) รอบแรกสคริปต์ไม่ได้ตอบสิทธิ จึงถูกปิดผลตามกฎ และ Chrome จากสคริปต์เปิดไม่ขึ้นในรอบหลัง จึงเปิดเองแล้วให้สคริปต์ต่อ
- [ ] Independent review เทียบกับ `b825c5a`; แก้ผลด้วย RED→GREEN
- [ ] `tgps-mark-progress` + DEC สถานะ IMPLEMENTED; user acceptance เปิดไว้
