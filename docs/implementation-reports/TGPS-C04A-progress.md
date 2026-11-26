# TGPS-C04A — Progress ledger

## 2026-11-26 — Requirement draft / DEC-037

- [x] ผู้ใช้ขอตัวช่วยลดหย่อนก่อนสิ้นปีและตอบ "โอเครครับ ลุย!" บันทึก [DEC-037](../DECISIONS.md#dec-037--open-c04a-thai-esg-year-end-what-if-requirement-review) และซิงก์ Roadmap
- [x] สำรวจโค้ดที่ `67208cc`: catalog `@1.2.0` มี `TH-OPP-THAI-ESG-2026` (rate 0.30, cap 300,000, holding 5 ปี, source `SEC-THAI-ESG-2026`); `candidate/engine.py` สร้างเฉพาะจำนวนขอบเขตบนเส้นทางเดโมเดิมและคำนวณผ่าน `TaxState.tax_impact`; `candidate/activation.py:69` ปฏิเสธ PVD บวกตาม C02A-AC06 (staging boundary จาก C02A requirement); เส้นทาง C03 ไม่มีข้อมูล guardrail
- [x] จัด [ร่าง C04A v0.1](../requirements/TGPS-C04A-thai-esg-year-end-what-if.md) ขอบเขต Thai ESG จำนวนเดียวบน C03, ข้อตัดสิน D1–D4, AC01–10, หลักฐาน E1–E2 เป็นเอกสารเท่านั้น ไม่มีการแก้โค้ด
- [ ] ผู้ใช้ตัดสิน D1–D4
- [ ] E1 ตรวจแหล่ง Thai ESG ปี 2569 ด้วย `tgps-policy-evidence`
- [ ] แผนและตัวอย่างคำนวณอิสระหลังรับ requirement

Current task: `REQUIREMENT_REVIEW` · implementation `NOT_STARTED`
