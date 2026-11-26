# C04A Thai ESG Year-End What-If Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task after plan approval. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ผู้ใช้ใส่จำนวนเงินที่จะซื้อ Thai ESG ภายในปี 2569 บนประมาณการ C03 แล้วเห็น PIT และยอดชำระเพิ่ม/คืน ก่อนและหลัง พร้อมวงเงินสิทธิและผลตรวจเงินสำรอง

**Architecture:** บริการ domain ใหม่รับ `AnnualEstimateResult` ที่ READY, จำนวนทดลอง, ยอดซื้อเดิม และ `FinancialProfile` วงเงินมาจาก `calculate_opportunity_capacity` เดิมด้วย catalog ที่ activate แล้ว เงินสำรองมาจาก `compute_financial_state` + `assess_new_cash_opportunity` เดิม และ PIT หลังซื้อมาจาก `calculate_tax_saving` เดิม ไม่มีสูตรภาษีหรือ guardrail ชุดที่สอง เส้นทางเดโมเดิม, `TaxState.tax_impact` และ candidate engine คง contract เดิม

**Tech Stack:** Python standard library, frozen dataclasses, `Money`/`Decimal`, pytest/Ruff/mypy, เดโม local HTTP + HTML/CSS/JS เดิม

**Spec:** [C04A v0.1](../../requirements/TGPS-C04A-thai-esg-year-end-what-if.md), [DEC-037](../../DECISIONS.md#dec-037--open-c04a-thai-esg-year-end-what-if-requirement-review), [DEC-038](../../DECISIONS.md#dec-038--c04a-review-decisions-d1d4-agreed), [หลักฐาน E1](../../policy-evidence/2026-11-26/README.md), [ตัวอย่างอ้างอิง](../../implementation-reports/TGPS-C04A-acceptance-reference.md)

**สถานะแผน:** `DRAFT_FOR_REVIEW` · D5 (Task 1B) และ D6 รอผู้ใช้ตัดสิน · implementation `NOT_STARTED`

## ข้อกำหนดร่วม

- ใช้ pack `TH-PIT-2026-001@1.2.0` และ catalog `TH-OPPORTUNITY-2026-001@1.2.0` เดิม ไม่ออก version ใหม่ใน v0.1 (D6 ข)
- ลำดับสถานะของส่วนทดลอง: C03 ไม่ READY → `UNSUPPORTED` → `REQUIRES_INPUT` → ข้อจำกัด (เกินวงเงิน / guardrail) → `READY` แยก `None` จากศูนย์ทุกช่อง
- ฐาน 30% ใช้ `tax.income.assessable_income` เหมือน discovery/candidate (PVD บวกจึงใช้เงินได้หลังส่วนยกเว้น PVD)
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
| 1 | Domain what-if (AC01–05, 07–09) | ยังไม่เริ่ม |
| 1B | คำถามสิทธิสับเปลี่ยน LTF→ESGX ใน C03 (D5, AC06) | รอ D5 |
| 2 | Snapshot, export, replay (AC10) | ยังไม่เริ่ม |
| 3 | HTTP และเดโมภาษาไทย (AC01–10) | ยังไม่เริ่ม |
| 4 | ตรวจรวม, Chrome, independent review | ยังไม่เริ่ม |

## Task 1 — Domain what-if

**ไฟล์:** สร้าง `src/tax_gps/candidate/thai_esg_what_if.py`, `tests/acceptance/test_c04a_thai_esg_what_if.py` · ถ้าตัวคำนวณส่วนต่างของ C03 เป็น private ให้แยกเป็นฟังก์ชันร่วมใน `annual_estimate.py` โดยไม่เปลี่ยนผล C03

**Interfaces ที่เสนอ**

- `WhatIfStatus(StrEnum)`: `BASELINE_NOT_READY`, `UNSUPPORTED`, `REQUIRES_INPUT`, `EXCEEDS_TAX_CAPACITY`, `GUARDRAIL_LIMITED`, `READY`
- Frozen `ThaiEsgWhatIfInput(amount: Money | None, prior_thai_esg_usage: Money | None, financial: FinancialProfile)`
- `evaluate_thai_esg_what_if(estimate: AnnualEstimateResult, inputs: ThaiEsgWhatIfInput, catalog: ActivatedOpportunityCatalog, financial_policy: ActivatedFinancialPolicy, planning_date: date) -> ThaiEsgWhatIfResult`
- Frozen `ThaiEsgWhatIfResult`: `status`, `reason_codes`, `missing_fact_ids`, `capacity: OpportunityCapacity | None`, `guardrail: GuardrailAssessment | None`, `amount`, `impact: TaxImpact | None`, `settlement_before/after` (kind + amount, `None` เมื่อยอดหักขาด), `conditions` (lock-up และ evidence จาก catalog)

**Steps**

- [ ] RED: `test_c04a_amount_impact_matches_reference` (ESG-0/100K/CAP), `test_c04a_capacity_boundary` (CAP, OVER-CAP), `test_c04a_forecast_edit_moves_capacity`, `test_c04a_withholding_missing_keeps_pit`, `test_c04a_prior_usage` (1/ว่าง/0), `test_c04a_guardrail_inputs_and_limits`, `test_c04a_pvd_open_rmf_closed`, `test_c04a_blocked_baseline_hides_everything`, `test_c04a_amount_validation` (ติดลบ, เกินสตางค์ = input error ระบุช่อง)
- [ ] รัน `uv run --locked pytest tests/acceptance/test_c04a_thai_esg_what_if.py -q` บันทึก RED (กรณีที่ผ่านตั้งแต่แรกบันทึกเป็น characterization)
- [ ] Implement: ตรวจ C03 READY และ planning availability → prior usage → amount/financial ว่าง → capacity (`calculate_opportunity_capacity` กับ definition `TH-OPP-THAI-ESG-2026`, `shared_amount_used = prior`) → financial state + `assess_new_cash_opportunity(NewCashInputs(..., remaining_capacity=capacity.remaining, available_budget=amount, state))` → ถ้า amount > capacity หรือ > `max_feasible_allocation` ให้สถานะข้อจำกัด → `calculate_tax_saving(tax.taxable_income, amount, tax._activated_pack)` → settlement ก่อน/หลังด้วยฟังก์ชันเดียวกับ C03
- [ ] GREEN targeted แล้ว `uv run --locked pytest -q`; บันทึก ledger

## Task 1B — สิทธิสับเปลี่ยน LTF→ESGX (เฉพาะเมื่อผู้ใช้ตกลง D5 ก)

**ไฟล์:** `src/tax_gps/calculation/annual_estimate.py`, `annual_estimate_audit.py`, `examples/annual_estimate_adapter.py`, tests C03 ที่เกี่ยวข้อง

- [ ] RED: C03 ตอบ มี → `UNSUPPORTED` reason `LTF_ESGX_SWITCH_EXEMPTION_UNSUPPORTED`; ยังไม่ทราบ → `REQUIRES_INPUT` fact `ltf_esgx_switch_exemption`; ไม่มี → ผลเดิมทุกตัวเลข; precedence กับ `ADVANCED_TAX_PATH_REQUIRED` คงเดิม
- [ ] เพิ่มฟิลด์ใน `AnnualEstimateRights` และ snapshot material; bump schema version ของ C03 snapshot และให้ replay ปฏิเสธ schema เดิมพร้อมข้อความชัด
- [ ] บันทึก revision ใน C03 requirement change log อ้าง DEC ของ D5; เส้นทางเดโมเดิมไม่เปลี่ยน

## Task 2 — Snapshot, export, replay

**ไฟล์:** สร้าง `src/tax_gps/candidate/thai_esg_what_if_audit.py`, `tests/acceptance/test_c04a_thai_esg_what_if_audit.py`

- [ ] RED: snapshot ผูก C03 snapshot hash, catalog content hash, financial policy hash, จำนวน, ยอดซื้อเดิม, financial profile material, ผลทั้งหมด; replay คำนวณซ้ำได้ผลเดิม; payload ที่แก้จำนวนแต่ใช้ hash เดิมถูกปฏิเสธ; สถานะไม่ READY ไม่มี snapshot
- [ ] Implement ด้วย `canonical_json` + `sha256_hex`; ไม่ใช้ `json.dumps` กับ model ที่ freeze
- [ ] GREEN และ full suite

## Task 3 — HTTP และเดโมภาษาไทย

**ไฟล์:** `examples/annual_estimate_adapter.py` (block `thai_esg_what_if` ที่เป็น optional ใน request เดิม), `examples/web/annual-estimate.js`, `examples/web/index.html`, `examples/web/profile.css`, `examples/demo_errors.py`, `tests/acceptance/test_c04a_thai_esg_what_if_demo.py`, `tests/web/test_app.cjs`

- [ ] RED HTTP: request ไม่มี block = response C03 เดิม byte-for-byte ในส่วน C03; block ครบ = ผลก่อน/หลังตามตัวอย่าง; ช่องผิด = error ระบุช่องโดยไม่สะท้อนค่า
- [ ] RED frontend: ส่วน "ทดลองซื้อ Thai ESG" แสดงหลัง C03 READY เท่านั้น; ช่องจำนวน, ยืนยันยอดซื้อเดิมปีนี้, เงินสดคงเหลือ, ค่าใช้จ่ายจำเป็นต่อเดือน, หนี้/ภาระจ่าย (ใช้ component เดิมของเดโม); ผลคู่ก่อน/หลัง; เงื่อนไขจาก catalog; แก้ข้อมูลแล้วผลและ export เก่าหาย; response ค้างไม่เผยผล
- [ ] Implement แล้วรัน `uv run --locked python -m examples.check_web_demo` (ห้ามรัน node ตรง)

## Task 4 — ตรวจรวมและส่งรีวิว

- [ ] `tgps-verify` ครบ 7 gates บันทึกตัวเลขจริง
- [ ] Chrome 1440/390, keyboard, reduced motion บน server ใหม่พอร์ตว่าง
- [ ] Independent review เทียบกับ `b825c5a`; แก้ผลด้วย RED→GREEN
- [ ] `tgps-mark-progress` + DEC สถานะ IMPLEMENTED; user acceptance เปิดไว้
