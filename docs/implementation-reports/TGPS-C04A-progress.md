# TGPS-C04A — Progress ledger

## 2026-11-26 — Requirement draft / DEC-037

- [x] ผู้ใช้ขอตัวช่วยลดหย่อนก่อนสิ้นปีและตอบ "โอเครครับ ลุย!" บันทึก [DEC-037](../DECISIONS.md#dec-037--open-c04a-thai-esg-year-end-what-if-requirement-review) และซิงก์ Roadmap
- [x] สำรวจโค้ดที่ `67208cc`: catalog `@1.2.0` มี `TH-OPP-THAI-ESG-2026` (rate 0.30, cap 300,000, holding 5 ปี, source `SEC-THAI-ESG-2026`); `candidate/engine.py` สร้างเฉพาะจำนวนขอบเขตบนเส้นทางเดโมเดิมและคำนวณผ่าน `TaxState.tax_impact`; `candidate/activation.py:69` ปฏิเสธ PVD บวกตาม C02A-AC06 (staging boundary จาก C02A requirement); เส้นทาง C03 ไม่มีข้อมูล guardrail
- [x] จัด [ร่าง C04A v0.1](../requirements/TGPS-C04A-thai-esg-year-end-what-if.md) ขอบเขต Thai ESG จำนวนเดียวบน C03, ข้อตัดสิน D1–D4, AC01–10, หลักฐาน E1–E2 เป็นเอกสารเท่านั้น ไม่มีการแก้โค้ด
- [x] ↳ ทำแล้ว: ผู้ใช้ตัดสิน D1–D4 (ดูหัวข้อถัดไป)
- [x] ↳ ทำแล้ว: E1 (ดูหัวข้อถัดไป)
- [x] ↳ ทำแล้ว: แผนและตัวอย่างอ้างอิง (ดูหัวข้อถัดไป)

## 2026-11-26 — D1–D4 agreed, E1 evidence, plan draft / DEC-038

- [x] ผู้ใช้ตอบ "ผมโอเครกับคุณทุกข้อครับ ลุยได้เลย!" บันทึก [DEC-038](../DECISIONS.md#dec-038--c04a-review-decisions-d1d4-agreed) ซิงก์ Roadmap, C04A v0.1 และเพิ่ม change log ใน C02A requirement (revision ของ AC06 เฉพาะเส้นทาง C04A)
- [x] E1 ด้วย `tgps-policy-evidence`: SEC Q&A PDF ยังดาวน์โหลดไม่ได้ (server ส่ง HTML 13,730 bytes) จึงใช้คำอธิบายแบบ ภ.ง.ด.94 ปีภาษี 2569 ของกรมสรรพากร (PDF 17 หน้า, SHA-256 `4de4d7e8…5b40`) หน้า 11 ข้อ 16.1–16.2 ยืนยัน 30% / 300,000 สำหรับการซื้อ 1 ม.ค. 2567–31 ธ.ค. 2569 และถือ 5 ปี หน้า 7–9 รายการวงเงินรวม 500,000 ไม่มี Thai ESG ตรวจจาก text extraction เท่านั้น (เครื่องไม่มี `pdftoppm` จึงตรวจภาพไม่ได้) บันทึกที่ [policy-evidence/2026-11-26](../policy-evidence/2026-11-26/README.md) catalog `@1.2.0` ไม่ถูกแก้
- [x] ข้อค้นพบ F1 (สิทธิสับเปลี่ยน LTF→ESGX ปี 2569–2572 ที่ baseline ไม่ได้ถาม) และ F2 (เงื่อนไขแจ้ง บลจ. ข้อ 16.7) เสนอเป็น D5/D6 ใน requirement รอผู้ใช้ตัดสิน F3 ไม่กระทบ v0.1 เพราะ D2
- [x] สำรวจโค้ดเพิ่ม: `TaxState.tax_impact` ปฏิเสธ PVD/RMF บวก (`calculation/models.py:162`) แผนจึงเรียก `calculate_tax_saving` ตรงและคง `tax_impact` เดิม; guardrail ใช้ `assess_new_cash_opportunity` ได้โดยไม่ต้องผ่าน discovery; ฐาน 30% ใช้ `tax.income.assessable_income` ตามเดิม
- [x] [ตัวอย่างอ้างอิง](TGPS-C04A-acceptance-reference.md) คำนวณด้วย `Decimal` แยกจาก `tax_gps` แล้วเทียบ `calculate_tax_saving` ได้ 5/5 ตรงกัน และ ESG-FORECAST-EDIT ตรงกับ engine (ร่างแรกเขียนวิธีคิดผิดหนึ่งจุด แก้แล้ว ผลไม่เปลี่ยน)
- [x] [แผน C04A](../superpowers/plans/2026-11-26-c04a-thai-esg-what-if.md) สี่ tasks + Task 1B แบบมีเงื่อนไข สถานะ `DRAFT_FOR_REVIEW`
- [ ] ↳ ย้ายไปหัวข้อถัดไป: ผู้ใช้ตัดสิน D5/D6 และอนุมัติแผน

Current task: `REQUIREMENT_REVIEW` (D5/D6) + plan `DRAFT_FOR_REVIEW` · implementation `NOT_STARTED` · ไม่มีการแก้โค้ดในรอบนี้

## 2026-11-26 — Review corrections before plan approval

- [x] Reviewer ชี้สี่ข้อ ตรวจในโค้ดแล้ว:
  1. ฐาน 30% ของ PVD บวกเป็นการตีความใหม่: engine ให้ assessable 970,500 สำหรับ C03 `pvd_input` (ตรวจด้วย `calculate_annual_estimate`; สคริปต์ตัวอย่างรอบแรกป้อนค่านี้เอง) เพิ่ม D7 และติดป้าย PVD-ESG-CAP เป็น provisional
  2. ยอดซื้อ Thai ESG เดิมเป็น fact ของ C03 อยู่แล้ว (`annual_estimate.py:82`, adapter `shared_usage`) ตัด input ซ้ำออกจากแผน AC07 คาดหวัง `BASELINE_NOT_READY` และให้ planning date มาจาก cutoff ของ C03
  3. RMF บวกปิดใน v0.1: ระบุใน AC09 ให้ตรงกับแผน
  4. F1 ผิด: C03 ถาม `other_rights.thai_esgx` และ `fund_history.ltf_carryforward` อยู่แล้ว (`calculation/readiness.py:101-112`) แก้ README หลักฐานและ D5 ด้วยขีดฆ่า + CORRECTION; D5 เหลือเพียงปรับข้อความบนจอ ไม่ต้องเปลี่ยน readiness หรือ snapshot
- [x] เพิ่มหมายเหตุว่า ภ.ง.ด.94 เป็นแบบครึ่งปีสำหรับ 40(5)–(8) และใช้อ้างเนื้อหากฎ Thai ESG เท่านั้น ระบุในแผนว่าเมื่อเกินทั้งวงเงินสิทธิและ guardrail ให้ `EXCEEDS_TAX_CAPACITY` ก่อน
- [ ] ผู้ใช้ตัดสิน D5/D6/D7, อนุมัติแผน และอนุญาต push ครั้งแรก

Current task: `REQUIREMENT_REVIEW` (D5–D7) + plan `DRAFT_FOR_REVIEW` · implementation `NOT_STARTED`

## 2026-11-27 — Native execution / DEC-039

- [x] ผู้ใช้ตกลง D5–D7, อนุมัติแผน และอนุญาต push บันทึก [DEC-039](../DECISIONS.md#dec-039--c04a-d5d7-agreed-plan-approved-and-native-implementation-started) push `feature/tgps-c01-baseline-integrity` ไป origin ที่ `a617c26` (`1063fef..a617c26`) ยังไม่ได้ตรวจผล CI ของ SHA นี้
- [x] Task 1 DONE (AC01–05, 07–09): RED collection ขาดโมดูล `tax_gps.candidate.thai_esg_what_if` → GREEN รอบแรก 20/25 (guardrail budget เกินเงินสดที่ทราบ, fixture 0.001) แก้แล้ว 25/25 ตัวเลขตรงกับ [ตัวอย่างอ้างอิง](TGPS-C04A-acceptance-reference.md) ทุกแถว รวม PVD-ESG-CAP (provisional, D7) Python 907 ผ่านใน 14.34s, coverage 3,493 statements / 1,014 branches ที่ 100%, ruff check/format 213 ไฟล์ และ mypy strict 130 ไฟล์ผ่าน บน Windows Python 3.14.3
- Ruling: guardrail budget = min(วงเงินสิทธิที่เหลือ, เงินสดคงเหลือ) เพราะ `compute_financial_state` ปฏิเสธ budget ที่เกินเงินสดที่ทราบ (fail closed เดิม) `max_feasible_allocation` จึงเป็นจำนวนสูงสุดที่ทั้งสิทธิและเงินสำรองอนุญาต
- Ruling: entry point รับ `AnnualEstimateInput` + pack แล้วคำนวณ C03 ภายใน แทนการรับผลจากภายนอก เพื่อไม่ให้ผลกับ input ขัดกัน ยอดซื้อ Thai ESG เดิมและวันวางแผนมาจาก C03

- [x] Task 1B DONE (D5): RED frontend 58/59 → GREEN 59/59 ผ่าน `examples.check_web_demo`; Python 907 ผ่าน ข้อความช่อง `fund_history_ltf_carryforward` ใช้ร่วมทั้งเส้นทางเดิมและ C03 ไม่เปลี่ยน id, readiness หรือ snapshot

Current task: Task 2 (snapshot/replay)

