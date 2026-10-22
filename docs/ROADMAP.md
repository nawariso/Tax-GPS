# Tax GPS — Product Roadmap

Version: `0.1`  
Updated: `2026-10-15` (Asia/Bangkok)  
Direction: **AGREED**  
Current work: **C01 IMPLEMENTED — Task 1–5 ทำ/ตรวจ/รายงานแล้ว; Python 694, coverage 100%, frontend 24/24; F09 OPEN / acceptance conditional, ยังไม่ ACCEPTED**

Presentation work: **TGPS-UI01 IMPLEMENTED / VISUAL_REVIEW_PENDING** — restyle และ automatic/source verification เสร็จแล้ว;
ดู [ข้อเสนอ UI01](requirements/TGPS-UI01-fintech-restyle.md) / [DEC-012](DECISIONS.md#dec-012--ทิศทางปรับหน้าตาตาม-fintech-template).
เปลี่ยนเฉพาะ presentation และไม่เปลี่ยนสถานะ/ลำดับ C01–C06

UI01 follow-up2026-10-20: ตรวจ rendered1440/390/360 และ keyboard แล้ว,
แก้ลายตกแต่งทำให้ mobile overflow; local695/coverage100%/frontend24 และทุก gate ผ่าน.
ยังรอ reduced-motion-mode check และ user visual acceptance;
ดู [rendered review](implementation-reports/TGPS-UI01-visual-review-2026-10-20.md).

Handoff: Windows Python3.14.3 และ isolated3.12.14 ผ่าน 695 tests, coverage100%,
frontend24/24 และทุก quality gate; remote Ubuntu/Node22 CI ยังไม่ได้รัน
([หลักฐาน](implementation-reports/TGPS-handoff-verification.json)).
C02 มี [requirement v0.1](requirements/TGPS-C02-existing-rights.md)
เป็น **REQUIREMENT_REVIEW / implementation NOT_STARTED**: scope/behavior approved
ตาม DEC-019; legal evidence gate ยัง OPEN

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
| 2026-10-22 | 0.1 | เพิ่มแบบ UX C02 สำหรับรีวิวตามคำขอความเข้าใจง่าย; ไม่เปลี่ยนสถานะ milestone | DEC-020 |
| 2026-10-22 | 0.1 | อนุมัติแบบ UX C02และทำprototypeสำหรับลอง; parent legal/treatment statusไม่เปลี่ยน | DEC-021 |
| 2026-10-22 | 0.1 | เสนอ C02A ordinaryPVD baselineเป็นขั้นแรก; ยังไม่อนุมัติ/เริ่ม implementation | DEC-022 AUTHORING_DETAIL |

## UI02 presentation follow-up — 2026-10-20

TGPS-UI02 **IMPLEMENTED / USER_VISUAL_ACCEPTANCE_PENDING**: guided form, auto450ms, stable pending shell และ motion ทำแล้วตามแบบที่อนุมัติ; Python695/coverage100%/frontend37/full gates ผ่าน. Chrome1440/390/360 ตรวจแล้ว; reduced-motion runtime pending. ไม่เปลี่ยน C01/C02–C06. ดู [รายงาน UI02](implementation-reports/TGPS-UI02.md).

UI02 follow-up 2026-10-21: reduced-motion runtime ตรวจผ่านใน Chrome DevTools
reduce emulation แล้ว พร้อม active CSS และ auto recalculation; คืน media/default
หลังตรวจ. Local Python695/coverage100%/frontend37 และทุก gate ผ่านบน source เดิม.
ยังรอ user visual acceptance; C01 F09/C02–C06 ไม่เปลี่ยน.
ดู [หลักฐานรอบติดตาม](implementation-reports/TGPS-UI02-follow-up-2026-10-21.md).

Checkpoint follow-up 2026-10-21 (DEC-018): UI code committed as `805e2d9`;
pre-commit Python695/frontend37 ผ่าน. C01 มี
[acceptance handoff review](implementation-reports/TGPS-C01-review-follow-up-2026-10-21.md)
และ C02 มี [review brief](requirements/TGPS-C02-review-brief.md) พร้อมรีวิวรายละเอียด;
สถานะ acceptance/F09/C02 implementation ไม่เปลี่ยน. Remote CI ของ checkpoint ใหม่รอตรวจ

Remote checkpoint result: head `951732e` / merge `c404f7a`,
[CI run13](https://github.com/nawariso/Tax-GPS/actions/runs/39628740428) SUCCESS:
Ubuntu24.04.5/Python3.12.15/Node22.23.3, Python695/coverage100%/frontend37
และทุก gate ผ่าน. เป็นผลของ SHA นี้เท่านั้น; ไม่ปิด F09/acceptance/C02 gates

## C02 evidence follow-up — 2026-10-21 (DEC-019)

ผู้ใช้อนุมัติ scope/behavior ของ requirement v0.1 แล้ว; สถานะยัง
REQUIREMENT_REVIEW (legal evidence review) / implementation NOT_STARTED.
จัด [primary-source matrix](policy-evidence/2026-10-21/README.md),12 original
artifactsพร้อมhash และ9 provisional numeric fixtures/independent arithmetic9/9แล้ว.
G1–G6ยังOPEN จึงยังไม่เขียนimplementation planหรือเพิ่มtreatment.
C01 acceptance/F09/UI visual acceptanceไม่เปลี่ยน

Follow-up2026-10-22: [cross-rule review](policy-evidence/2026-10-21/joint-follow-up/README.md)
ตรวจ MR266→MR357 และเทียบ SEC QA/MR398/DG458 สำหรับ ESGX2026 common pool;
custody19 originals (รวม unrelated sourceที่คัดออก),4 diagnostic casesเพิ่มแยกจาก9เดิม.
RMF basisสองสมมติฐานให้ PITต่าง2700บาท จึงยังไม่เลือกสูตร;
PVD aggregation/exception และ independent/current-applicability gatesยังOPEN.
ไม่มีการเปลี่ยน milestone หรือ implementation status

UX follow-up2026-10-22 (DEC-020): ตามคำขอให้อ่านง่าย จัด
[C02 guided-rights UX draft](requirements/TGPS-C02-guided-rights-ux.md)
เป็น REQUIREMENT_REVIEW: ภาพรวม→สิทธิ→วิธีคิด, unknown/zeroชัด, errorพาไปฟิลด์;
เป็นข้อเสนอหน้าจอ ไม่ใช่ implementation plan และไม่ปิด legal gates.

UX follow-up (DEC-021): ผู้ใช้อนุมัติแบบแล้ว; มี
[clickable prototype](demo/c02-guided-rights-preview.html) และfield/copy inventory.
ตรวจChrome390/320pxและinteractionหลักแล้ว; ไม่เชื่อมtax engine/เพิ่มAPI,
ไม่อ้างว่าC02IMPLEMENTED และยังไม่ผ่านuser usability acceptance

Evidence follow-up: [SETworkedexamples](policy-evidence/2026-10-22/README.md)
เพิ่มcorroborationของgrossRMFbase แต่ไม่ปิดG1/G3; custody22originalsรวม
supplementary/excluded sources. [C02Aproposal](requirements/TGPS-C02A-pvd-first-slice.md)
พร้อมscope review ไม่ใช่การเปลี่ยนparentcoverageหรือimplementationplan

2026-10-22 / DEC-023: ผู้ใช้อนุมัติ C02A v0.1 แล้ว — PVD นายจ้างเดียว/
กองทุนเดียว/อัตราปกติเป็นขั้นแรก; positive PVD แสดง baseline ก่อนและยังไม่เปิด
ทดลองเงินใหม่. Scoped evidence review OPEN / implementation NOT_STARTED;
parent C02 และ acceptance เดิมไม่เปลี่ยน

2026-10-22 / DEC-024: Scoped chain/currency และ normal-PVD reference9/9
เพียงพอสำหรับ planning เท่านั้น; [แผน C02A 4tasks](superpowers/plans/2026-10-22-c02a-normal-pvd.md)
เป็น DRAFT_FOR_REVIEW / implementation NOT_STARTED. Parent legal gates ไม่ถูกปิดรวม

## Current checkpoint — 2026-10-22 / DEC-025–026

C02A implementation **IN_PROGRESS**: core/consumer Tasks1–2 complete; integrated Thai UI implemented and reviewed, Tasks3–4 retain request-size and reduced-motion verification/documentation work. Python752/coverage100%/frontend45 pass all seven local gates. User authorized commit/push and continuation. Parent C02 remains legal REQUIREMENT_REVIEW, C01/F09 and user acceptance remain open. Earlier NOT_STARTED/plan-review summaries are historical and superseded for C02A only.
