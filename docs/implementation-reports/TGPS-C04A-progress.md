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

- [x] Task 2 DONE (AC10): RED collection ขาดโมดูล audit → GREEN 17/17 แล้วเพิ่ม malformed cases ปิด coverage → 20/20; Python 927 ผ่านใน 13.87s, coverage 3,558 statements / 1,024 branches 100%, ruff 215 ไฟล์, mypy strict 132 ไฟล์ผ่าน Snapshot schema `tax-gps-thai-esg-what-if/1` ผูก engine `tax-gps-thai-esg-what-if/0.1.0`, catalog และ financial policy hash, ฝัง C03 snapshot ทั้งชุด สถานะไม่ READY ไม่มี export

- [x] Task 3 DONE (AC01–10): HTTP RED 15/16 fail (1 characterization: ไม่มี block = response C03 เดิม) → GREEN 16/16; frontend RED 7 fail → GREEN 66/66 ผ่าน `examples.check_web_demo` request C03 รับ block `thai_esg_what_if` แบบ optional, error ภาษาไทยไม่สะท้อนค่าที่กรอก, export what-if ฝัง C03 snapshot ช่องการเงินในหัวข้อ 3 ใช้ร่วมกับเส้นทางเดิม (ซ่อนงบทดลองในโหมดทั้งปี) ตรวจครบ 7 gates: ruff 216 ไฟล์, format, mypy strict 133 ไฟล์, Python 943 ผ่านใน 14.29s, coverage 3,558 statements / 1,024 branches 100%, frontend 66/66 (0 fail/0 skip), build wheel/sdist 0.4.0

- [x] Task 4 Chrome: headless Chrome 158 ผ่าน CDP บน server ใหม่ ตรวจ 1440/390, over-cap, ยอดว่าง, reduced motion และ keyboard ผลตรงตัวอย่างอ้างอิง overflow 0 ([receipt](TGPS-C04A-chrome-2026-11-27.json)) รอบแรกสคริปต์ไม่ได้ตอบคำถามสิทธิ จึงถูกปิดผลตามกฎ (ไม่ใช่ bug) และ Chrome ที่สคริปต์เปิดเองเปิดไม่ขึ้นในรอบหลัง จึงเปิด Chrome เองแล้วให้สคริปต์ต่อ ปิด Chrome และ server ที่เปิดไว้แล้ว

- [x] Task 4 review (advisor reviewer model ที่เห็น transcript ทั้งหมด ไม่ใช่ human review) พบ 3 ข้อ แก้ใน `652d4b9`:
  1. ค่าตัวอย่างเงินสด 500,000 / ค่าใช้จ่าย 50,000 ของเดโมถูกใช้ใน guardrail ทั้งที่ผู้ใช้ไม่ได้กรอก (ขัด D3) → frontend RED 2 → GREEN: โหมดทั้งปีล้างค่าที่ผู้ใช้ยังไม่แก้และคืนค่าเมื่อกลับเส้นทางเดิม ค่าที่ผู้ใช้แก้แล้วคงไว้
  2. ช่อง what-if ที่ผิดรูปแบบ (ยอด, เงินสด, แถวหนี้, รูปแบบ block) ทำให้ทั้ง request 400 และผล C03 หาย → HTTP RED 5 + frontend RED 1 → GREEN: block ได้สถานะ `INVALID_INPUT` พร้อมชื่อช่องและข้อความไทยที่ไม่สะท้อนค่า ผล C03 และ export คงอยู่ (test HTTP เดิมที่คาด `DemoInputError` เปลี่ยนความหมายตาม AC08 นี้)
  3. วันตัด 31 ธ.ค. และภาระจ่ายที่เลยกำหนดก่อนวันตัดยังไม่มี test → domain 2 + HTTP 1 ผ่านตั้งแต่แรก (characterization): วงเงินมาจากเงินได้จริงทั้งปี และ `compute_financial_state` ไม่นับภาระที่เลยกำหนดเป็นเงินกันไว้
- [x] ตรวจครบ 7 gates ที่ `652d4b9` บน Windows Python 3.14.3 / Node 24.3.0: ruff 216 ไฟล์, format, mypy strict 133 ไฟล์, Python 946 ผ่าน, coverage 3,558 statements / 1,024 branches 100%, frontend 69/69 (0 fail/0 skip), build 0.4.0 Chrome receipt ตรวจที่ `6839686` ก่อนแก้ข้อ 1–2 ส่วนที่แก้ครอบคลุมด้วย frontend test (ไม่ได้ render ซ้ำ) และแก้ note ใน receipt ว่า `#error.hidden` ไม่ได้ตรวจตรง
- Known gaps (ไม่บล็อก ส่งให้ผู้ใช้รีวิว): แสดงวงเงินสิทธิที่เหลือก่อนซื้อเท่านั้น ยังไม่แสดงวงเงินหลังซื้อ; เหตุผลด้าน protection gap จาก guardrail ยังไม่แสดงในส่วน what-if; หน้ามือถือ 390px ตัวเลขขึ้นบรรทัดใหม่ที่คำว่า "บาท"
- [x] push `a617c26..652d4b9` ไป origin PR #4 รัน CI (pull_request) run `45868522352` บน `652d4b9`

- [x] CI PR #4 [run 45868522352](https://github.com/nawariso/Tax-GPS/actions/runs/45868522352) บน `652d4b9`: completed / success, job "Python 3.12 quality gates" ทุก step success (อ่านผ่าน GitHub API แบบไม่ยืนยันตัวตน จึงไม่เห็นจำนวน test ใน log) บันทึก [DEC-040](../DECISIONS.md#dec-040--c04a-implemented-locally) และซิงก์ Roadmap, requirement, plan และ README

Current task: C04A `IMPLEMENTED` · รอผู้ใช้ลองเดโมและรับงาน


## 2026-11-27 — บันทึกพักงานและจุดรับช่วง

ผู้ใช้ขอให้บันทึกไว้เพื่อกลับมาทำต่อ หยุดที่ C04A `IMPLEMENTED` / user acceptance `OPEN` ตาม [DEC-040](../DECISIONS.md#dec-040--c04a-implemented-locally)

- Git: `feature/tgps-c01-baseline-integrity` ที่ `847dffb` ตรงกับ origin (PR #4 เปิดอยู่ ยังไม่ merge) Working tree สะอาด ยกเว้น `docs/demo/stage4-local-profile-contract-draft.md` ที่เป็น untracked ของเดิม ไม่เกี่ยวกับงานนี้
- CI: PR #4 run [45868522352](https://github.com/nawariso/Tax-GPS/actions/runs/45868522352) บน `652d4b9` (โค้ดล่าสุด) success และ run [45868823374](https://github.com/nawariso/Tax-GPS/actions/runs/45868823374) บน `847dffb` (เอกสาร) success ตรวจผ่าน GitHub API เมื่อ 2026-11-27
- Local gates ล่าสุดที่ `652d4b9`: Python 946, coverage 100%, frontend 69/69, ruff/mypy/build ผ่าน (Windows Python 3.14.3 / Node 24.3.0)

เมื่อกลับมา ให้เริ่มตามลำดับนี้

1. รัน `tgps-session-start` (baseline ควรได้ Python 946 / frontend 69)
2. ถามผลการลองเดโมของผู้ใช้กับตัวเลขจริง (C03 + C04A) และถามข้อเท็จจริงที่ยังไม่ได้คำตอบ: มี PVD หรือไม่ ปีนี้ซื้อ RMF หรือ Thai ESG ไปแล้วหรือยัง ถ้าผู้ใช้ยืนยันรับงาน ให้บันทึก DEC สถานะ ACCEPTED แยกของ C03 และ C04A
3. Known gaps ที่ยังเปิด (ไม่บล็อก): แสดงวงเงินสิทธิที่เหลือหลังซื้อ, แสดงเหตุผล protection gap ในส่วนทดลอง, ตัวเลขบนมือถือ 390px ขึ้นบรรทัดที่คำว่า "บาท" และยังไม่ได้ render หน้า Chrome ซ้ำหลังแก้ผลรีวิวใน `652d4b9`
4. งานถัดไปที่เป็นไปได้ (ต้องมี requirement/DEC ก่อน): C04B RMF ซื้อเพิ่ม (ติดคำถามหลักฐาน PVD ร่วม RMF ตาม DEC-033), หลักฐานฐาน 30% ของ PVD บวก (D7), D6 เงื่อนไขแจ้ง บลจ. ใน catalog version ใหม่, รองรับยอดซื้อ Thai ESG เดิม (D2 ข / C04A.1)
5. งานเดิมที่ยังเปิด: C02A/C02B user acceptance, C02 legal G1–G6, C01/F09, การ merge PR #4 เข้า `main` ต้องให้ผู้ใช้ตัดสิน
