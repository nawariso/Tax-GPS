# Tax GPS — Product Roadmap

Version: `0.1`  
Updated: `2026-10-15` (Asia/Bangkok)  
Direction: **AGREED**  
Current work: **C01 IMPLEMENTED — Task 1–5 ทำ/ตรวจ/รายงานแล้ว; Python 694, coverage 100%, frontend 24/24; F09 OPEN / acceptance conditional, ยังไม่ ACCEPTED**

Presentation work: **TGPS-UI01 IMPLEMENTED / VISUAL_REVIEW_PENDING** — restyle และ automatic/source verification เสร็จแล้ว;
ดู [ข้อเสนอ UI01](requirements/TGPS-UI01-fintech-restyle.md) / [DEC-012](DECISIONS.md#dec-012--ทิศทางปรับหน้าตาตาม-fintech-template).
เปลี่ยนเฉพาะ presentation และไม่เปลี่ยนสถานะ/ลำดับ C01–C06

Handoff: Windows Python3.14.3 และ isolated3.12.14 ผ่าน 695 tests, coverage100%,
frontend24/24 และทุก quality gate; remote Ubuntu/Node22 CI ยังไม่ได้รัน
([หลักฐาน](implementation-reports/TGPS-handoff-verification.json)).
C02 มี [requirement v0.1-draft](requirements/TGPS-C02-existing-rights.md)
เป็น **REQUIREMENT_REVIEW / implementation NOT_STARTED** ตาม DEC-015

Remote follow-up: [draft PR#4](https://github.com/nawariso/Tax-GPS/pull/4),
[CI run10](https://github.com/nawariso/Tax-GPS/actions/runs/38765573860) SUCCESS
สำหรับ head c4527c9 (merge-ref b9015a3), Ubuntu24.04.5/Python3.12.15/Node22.23.3:
695 tests/coverage100%/frontend24 และทุก gate ผ่าน. เป็นหลักฐานเพิ่มหลัง handoff เดิม;
ไม่เปลี่ยน F09/visual acceptance หรือสถานะ C02. ดู [CI evidence](implementation-reports/TGPS-remote-ci.json)

## 1. ข้อตกลงและเป้าหมาย

ผู้ใช้ตกลง roadmap หกช่วงและให้จัดทำ requirement ช่วงแรกในบทสนทนาวันที่
15 ตุลาคม 2026 เป้าหมายของผลิตภัณฑ์คือ:

1. ประมาณภาระภาษีประจำปี พร้อมยอดที่คาดว่าจะชำระเพิ่มหรือได้รับคืน
2. รวมสิทธิจากรายการที่มีอยู่หรือจ่ายไปแล้วให้ถูกต้องในขอบเขตที่รองรับ
3. เปรียบเทียบการใช้เงินก้อนใหม่จากภาษี สภาพคล่อง สินทรัพย์ หนี้ และกำหนดใช้เงิน

MVP แรกเริ่มที่พนักงานเงินเดือน Section 40(1), ปีภาษี ค.ศ. 2026 / พ.ศ. 2569
ใช้ Python core และ local web demo ที่มีอยู่เป็นฐาน
การเลือกผู้ใช้กลุ่มนี้เป็นขอบเขตเริ่มต้น ไม่ใช่ข้อสรุปว่าทุกโปรไฟล์พนักงานรองรับแล้ว

ที่มาของข้อตกลงอยู่ใน [Decision Log](DECISIONS.md)
ข้อค้นพบและหลักฐานอยู่ใน [Product / Domain Review](reviews/2026-10-15-product-domain-review.md)

## 2. สถานะต้องแยกกัน

| สถานะ | ความหมาย |
| --- | --- |
| AGREED_DIRECTION | ตกลงเป้าหมายและลำดับงานแล้ว |
| REQUIREMENT_REVIEW | มี requirement รายละเอียดให้รีวิวแล้ว |
| PLANNED | ยังไม่ได้จัดทำ requirement รายละเอียดหรือเริ่มพัฒนา |
| IN_PROGRESS | เริ่ม implementation ตาม requirement ที่ตกลงแล้ว |
| IMPLEMENTED | มีโค้ดและหลักฐานตรวจในเครื่อง ยังอาจรอการรับงาน |
| ACCEPTED | ผ่านเกณฑ์รับงานและมี review record อ้างอิง |

การผ่าน tests ไม่เลื่อน milestone เป็น ACCEPTED โดยอัตโนมัติ
เอกสารระบุเฉพาะหลักฐานที่มีอยู่จริง; gate ที่ยังไม่ตรวจต้องแสดงตามจริง

## 3. Roadmap ที่ตกลง

| ID | ช่วง | ขอบเขตหลัก | เกณฑ์ออกจากช่วง | สถานะ |
| --- | --- | --- | --- | --- |
| TGPS-C01 | ความถูกต้องของฐานปัจจุบัน | ปิดความไม่สอดคล้อง retirement, shared usage, unknown eligibility, provenance และตรวจ HTTP failure | core/UI ปิดผลที่ไม่ครบตรงกัน, supported golden cases ถูกต้อง, version/replay ตรวจได้, failure มีข้อสรุปและหลักฐาน | IMPLEMENTED (Task 1–5 ตรวจแล้ว; F09 OPEN / acceptance conditional; [report](implementation-reports/TGPS-C01.md), [review](implementation-reports/TGPS-C01-review.md)) |
| TGPS-C02 | สิทธิเดิมของพนักงาน | รายการสิทธิที่จ่ายแล้ว เริ่ม PVD/RMF/Thai ESG; ต่อประกันและสิทธิครอบครัวเป็นงานย่อย | รายการที่รองรับลดฐานภาษีและใช้ capacity ครั้งเดียว; ระบุ missing/unsupported coverage; fixtures ตรวจตัวเลขโดยอิสระ | REQUIREMENT_REVIEW / implementation NOT_STARTED ([draft](requirements/TGPS-C02-existing-rights.md)) |
| TGPS-C03 | ประมาณการภาษีทั้งปี | actual/forecast, โบนัส, withholding ที่รองรับ | แสดง annual PIT แยกยอดชำระเพิ่ม/คืน; unknown ไม่เป็นศูนย์; forecast ไม่แก้ actual | PLANNED |
| TGPS-C04 | ทดลองใช้เงินก้อนใหม่ | จำนวนเงินที่ผู้ใช้เลือกบน budget เดิม; เพิ่มทางเลือก Thai ESG/RMF/ordinary investment/โปะหนี้ทีละประเภท | ทุก action มี tax/asset/debt treatment ตรงประเภท; เงินที่ไม่ใช้คงอยู่; ข้อจำกัดเงินสำรองยังทำงาน | PLANNED |
| TGPS-C05 | ความคุ้มตามเวลา | horizon, unlock dates, fees, cash-flow scenarios และ break-even | ใช้ horizon เดียวกัน, ไม่บวก tax cash ซ้ำหรือใช้ก่อนมีจริง, แสดง assumption/risk และทางเลือกตามเป้าหมาย | PLANNED |
| TGPS-C06 | ใช้งานต่อเนื่อง | local profiles, แผนหลายปี และเพิ่มปีที่มี policy ตรวจแล้ว | เปิด/บันทึก/ลบถูกต้อง, privacy/storage ชัด, ผลเก่าไม่ถูกใช้เป็นผลปัจจุบันโดยไม่คำนวณใหม่ | PLANNED |

ยังไม่กำหนดวันเสร็จหรือจำนวนสัปดาห์ เพราะรายละเอียดและปริมาณกฎหมายของช่วงถัดไป
ยังไม่ได้ตกลง ต้องใช้ผล C01 และขนาดงานย่อยประกอบก่อนกำหนดเวลา

## 4. ความสัมพันธ์ของงานและ MVP

```text
C01 ความถูกต้อง
  ↓
C02 สิทธิเดิมครบในขอบเขตที่เลือก
  ↓
C03 ภาษีทั้งปีและยอดชำระเพิ่ม/คืน       ← MVP สำหรับดูภาษี
  ↓
C04 ทดลองจัดสรรเงิน
  ↓
C05 เปรียบเทียบตามเวลาและเป้าหมาย     ← MVP สำหรับเปรียบเทียบการใช้เงิน
  ↓
C06 การใช้งานต่อเนื่องและหลายปี
```

C02 แบ่งเป็น requirement ย่อยได้; ต้องกำหนดรายการสิทธิของ MVP ที่รองรับให้ชัด
ก่อนอ้างว่าจบช่วง ไม่ถือว่าพนักงานทุกคนรองรับเพราะมี salary calculation

การบันทึก draft ขนาดเล็กอาจแทรกระหว่างช่วงได้เมื่อจำเป็นต่อการทดลองซ้ำ
ต้องมี requirement แยกและบันทึกการเปลี่ยนลำดับใน Decision Log
ยังไม่ได้เริ่มหรืออนุมัติรายละเอียด Stage 4 storage จากการตกลง roadmap นี้
ใช้ [Stage 4 draft](demo/stage4-local-profile-contract-draft.md) เป็นข้อมูลอ้างอิงต่อได้

## 5. งานที่ทำต่อทันที

งานแรกคือ [TGPS-C01 — Baseline Integrity](requirements/TGPS-C01-baseline-integrity.md)
แก้ความถูกต้องและขอบเขตการเผยผลของความสามารถปัจจุบัน
การรองรับ deduction จริงประเภทใหม่อยู่ C02 ไม่ควรแทรกเข้ามาโดยไม่มี requirement

C01 ทำ implementation/verification และ fresh review fix-pass แล้วตาม [report](implementation-reports/TGPS-C01.md)
จุดรับช่วงคือ review/acceptance และติดตาม F09 ที่ยัง OPEN; ไม่ต้องเริ่ม Task 1–5 ใหม่
เพียงเพราะ milestone ยังไม่ ACCEPTED. C02 จัดร่าง requirement สิทธิเดิมแล้ว; ต้องรีวิว
ขอบเขต/หลักฐานก่อนเพิ่ม treatment; การเปลี่ยนผลภาษี ขอบเขต หรือ readiness ต้องมี DEC ใหม่

## 6. ความสัมพันธ์กับ milestone เดิม

P1-001 ถึง P1-004 เป็นฐาน domain contracts ที่มีอยู่; C01–C06 เป็นชื่อของงานต่อจาก
product review ครั้งนี้ ไม่ใช่การเปลี่ยนชื่อหรือรับรอง milestone เก่าใหม่

- P1-004 ยังระบุ independent acceptance pending ใน requirement เดิม
- C01 เปลี่ยนเฉพาะสัญญาที่ระบุชัดใน requirement C01 พร้อมเวอร์ชันและ migration
- ฟีเจอร์เดิมนอกขอบเขต C01 ยังใช้สัญญาเดิม
- การรับงาน C01 ไม่เท่ากับการปิด gate ของ P1-004 หรือ production approval

## 7. วิธีรักษาประวัติและรีวิว

Requirement แต่ละฉบับต้องมี ID, version, status, scope, input/output behavior,
acceptance cases, dependencies และ change log
รายงาน implementation ต้องอ้าง version ของ requirement และ commit ที่ตรวจจริง

เมื่อเปลี่ยนเป้าหมาย ลำดับงาน หรือขอบเขต ให้เพิ่มรายการใน Decision Log พร้อมเหตุผล
แก้ roadmap ปัจจุบันให้ตรงกับการตัดสินใจ และเก็บ change log ของ requirement ที่ได้รับผล
ไม่เขียนทับประวัติให้ดูเหมือนเคยตกลงเช่นนั้นตั้งแต่แรก

## Change log

| Date | Version | Change | Basis |
| --- | --- | --- | --- |
| 2026-10-15 | 0.1 | บันทึก roadmap หกช่วง, MVP boundaries และ C01 เป็นงานแรก | ผู้ใช้ตกลงทิศทางในบทสนทนา; [DEC-001](DECISIONS.md#dec-001--roadmap-และผู้ใช้กลุ่มแรก) |
| 2026-10-15 | 0.1 | C01 เป็น IN_PROGRESS ตามหลักฐานใน ledger; ไม่เปลี่ยนลำดับหรือขอบเขต | [DEC-009](DECISIONS.md#dec-009--เริ่ม-implementation-c01-และการติดตามความคืบหน้า) |
| 2026-10-15 | 0.1 | C01 IMPLEMENTED ตาม local gates/fresh-review fix-pass; F09 OPEN และ acceptance conditional, C02 ยัง PLANNED | [DEC-011](DECISIONS.md#dec-011--c01-implemented-และจุดรับช่วงที่ไม่ทำงานเดิมซ้ำ) |
| 2026-10-15 | 0.1 | เพิ่ม local Python3.12 evidence และ C02 REQUIREMENT_REVIEW; ไม่เพิ่ม treatment หรือปิด acceptance | DEC-015 / handoff verification |
