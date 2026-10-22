# TGPS-C02 — สิทธิเดิมของพนักงาน

Version: `0.1`
Date: `2026-10-15` (Asia/Bangkok)
Direction: **AGREED_DIRECTION** ตาม roadmap
Detailed requirement: **REQUIREMENT_REVIEW** — ผู้ใช้อนุมัติ scope/behavior 2026-10-21; legal evidence review ยังไม่ผ่าน
Implementation: **NOT_STARTED** — ยังไม่อนุมัติ treatment ใหม่

## 1. เป้าหมายและฐานตั้งต้น

ผู้มีเงินได้มาตรา 40(1) ปีภาษี 2569 ระบุเงินสะสม/เงินลงทุนที่จ่ายไปแล้ว
เพื่อให้ baseline รวมสิทธิที่รองรับอย่างถูกต้อง และ discovery เห็นวงเงินคงเหลือ
จากผล baseline เดียวกัน ไม่หักภาษีซ้ำและไม่หักเงินจ่ายเก่าออกจาก budget ใหม่อีก
เริ่ม PVD (เฉพาะเงินสะสมลูกจ้าง), RMF และ Thai ESG ตาม roadmap;
ประกันและสิทธิครอบครัวใหม่ต้องมี requirement ย่อยก่อนเพิ่ม treatment

ต่อจาก C01 IMPLEMENTED ซึ่งยังมี F09 OPEN / acceptance conditional และ
UI01 IMPLEMENTED / visual acceptance pending. การเขียนร่างนี้ไม่ปิดสอง gate นั้น
และไม่อนุญาตให้ข้าม acceptance C01 เพื่อ release C02

## 2. ขอบเขตและวิธีที่เสนอ

- ใช้ Python core/typed immutable models/Money/Decimal และ presentation adapter เดิม
  ไม่เพิ่ม runtime dependency, network, clock, random, storage หรือ generic rules DSL
- ทำทีละประเภทโดยตรวจหลักฐานและ acceptance ของประเภทนั้นก่อน; ลำดับเสนอคือ
  PVD → RMF → Thai ESG เพื่อจัด retirement capacity ให้ถูกก่อนขยายสิทธิ
  ไม่ถือว่าประเภทใดรองรับจน implementation และ review ของประเภทนั้นครบ
- แยกยอดจ่ายจริง, ยอดเข้าเกณฑ์, ยอดใช้สิทธิจริง และยอดเกินเพดานให้ตรวจย้อนกลับได้
  ผล calculation/provenance ต้องระบุ rule version และเหตุผลที่ตัดยอด
- เป็นการคำนวณสิทธิเดิม ไม่จัดอันดับ ไม่แนะนำซื้อ ไม่เลือกผลิตภัณฑ์
  ไม่คำนวณผลตอบแทน ไม่เพิ่ม action การลงทุนใหม่ใน C04 และไม่คำนวณยอดคืนภาษีใน C03

## 3. ข้อมูลและ readiness

ข้อมูลแต่ละประเภทต้องแยกปีภาษี ยอดที่ผู้เสียภาษีจ่ายเอง และข้อเท็จจริง eligibility
ที่กฎของประเภทนั้นต้องใช้; PVD แยกเงินลูกจ้างออกจากเงินนายจ้างอย่างชัดเจน
RMF/Thai ESG ต้องแยกการซื้อใหม่จากยอดถือครองเก่า การโอน และการขายคืน
UI ระบุชื่อรายการที่ขาดหรือยังไม่รองรับ ไม่แสดงแค่ “ข้อมูลไม่ครบ”

`None`/ช่องว่างคือ unknown; explicit zero หมายถึงผู้ใช้ยืนยันไม่มีรายการเท่านั้น
ไม่มี default เป็นศูนย์หรือ eligible. eligibility false กับ unknown ต้องให้เหตุผลต่างกัน
หากยังไม่ทราบข้อเท็จจริงที่กระทบ baseline ให้ REQUIRES_INPUT;
รายการที่มีผลแต่ treatment ยังไม่รองรับให้ UNSUPPORTED ตาม domain
คง precedence ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY
และปิด PIT/taxable/saving/candidates/export เมื่อ baseline ไม่ READY

ต้องมี inventory ของรายการอื่นที่กระทบวงเงินร่วมตามกฎหมาย เช่น กบข., กองทุนครู,
กอช. และประกันบำนาญ โดยตรวจรายชื่อและผลของแต่ละประเภทก่อนอนุมัติ evidence gate
unknown ห้ามถือว่าไม่มี; positive ที่ยังไม่รองรับต้อง fail closed ไม่เอาแค่ยอดมาใช้
capacity แล้วละผลภาษีไว้. ห้ามใช้ช่อง shared usage เป็นทางลัดแทนการคำนวณสิทธิจริง

## 4. กติกาที่ต้องพิสูจน์ก่อนลงโค้ด

### PVD

หักเฉพาะเงินสะสมลูกจ้างที่เข้าเงื่อนไข แยก allowance กับ income exemption
และวาง exemption ให้ถูกก่อนคำนวณ expense ตามลำดับกฎหมาย
ห้ามนำยอดทั้งก้อนไปลดหลัง expense โดยไม่มีการพิสูจน์
ต้องยืนยันฐานค่าจ้างที่ใช้เพดาน, การรวมหลายนายจ้าง, เพดานประเภทและเพดานร่วม
รวมถึงกรณีเงินจ่ายจริงเกินสิทธิและค่าจ้างต่ำที่ expense ยังไม่ชนเพดาน
การรับเงินออก/เกษียณ/โอนออกและการแก้การใช้สิทธิย้อนหลังอยู่นอก scope
หากเกิดกรณีนั้นและกระทบ baseline ต้องแสดง unsupported/advanced ตาม domain

### RMF

แยกยอดซื้อในปีจากยอดถือครองเดิม ยืนยันฐานเงินได้สำหรับ percentage cap
และการรวมกับสิทธิเกษียณอื่น ใช้เงื่อนไขที่มีผลปี 2569 เท่านั้น
การซื้อสม่ำเสมอ การถือครอง การขายคืน และการส่งข้อมูลใช้สิทธิ
ต้องมีข้อเท็จจริงครบตาม supported coverage; ห้ามตีความ unknown ว่าเข้าเงื่อนไข
การ recapture/ผิดเงื่อนไขย้อนหลังอยู่นอก scope และต้อง fail closed เมื่อเกี่ยวข้อง

### Thai ESG

แยกปีซื้อและชนิดสิทธิ ไม่เอายอดถือครองเก่ามาลดหย่อนปีปัจจุบัน
ต้องยืนยันการใช้เพดานร่วมกับการซื้อ Thai ESGX ปี 2569 และแยกจากสิทธิโอน LTF
ห้ามอนุมานว่า Thai ESGX หรือ carry-forward LTF รองรับเพราะมีช่อง shared usage
รายการเหล่านี้ที่มีผลต่อ baseline ยังปิดผลจนมี treatment ที่อนุมัติ

### วงเงินร่วมและยอดจ่ายเกิน

ใช้ accepted claims ที่คำนวณจาก facts เดียวกับ baseline เป็น authority ของ capacity
ห้ามนำยอด arbitrary จาก caller มาลดยอดวงเงินเฉย ๆ หรือรับ snapshot ที่ต่างปี/version
ห้าม claim รวมเกินเพดาน และห้ามจัดลำดับรายการเองเพื่อเลือกผลภาษีที่ดีที่สุด
ถ้ากฎหมายกำหนดลำดับให้ทำตามลำดับนั้นพร้อมหลักฐาน; ถ้ามีหลายการเลือกที่ถูกกฎหมาย
และให้ผลต่างกัน ต้องจัด requirement revision สำหรับ explicit taxpayer election ก่อน
กรณีนั้นยังไม่รองรับในรุ่นแรก ไม่ silently เลือกตาม input order

## 5. Acceptance cases ที่ต้องผูก RED → GREEN

| ID | กรณี | ผลที่ต้องตรวจ |
| --- | --- | --- |
| C02-AC01 | PVD/RMF/Thai ESG เป็น unknown เทียบ explicit zero | missing IDs/เหตุผลถูกประเภท; unknown ไม่เท่าศูนย์; zero ไม่สร้าง deduction |
| C02-AC02 | positive แต่ eligibility unknown/false | unknown ปิดผล; false ไม่ให้สิทธิ พร้อมเหตุผลและการจัดการกรณีผิดเงื่อนไขตาม coverage ที่อนุมัติ |
| C02-AC03 | เงินสะสมลูกจ้าง PVD และเงินสมทบนายจ้าง | ไม่ให้สิทธิจากเงินนายจ้าง; แยกฐาน/รายการและเพดานตาม rule |
| C02-AC04 | PVD ค่าจ้างต่ำและหลายระดับเพดาน | fixture อิสระตรวจ exemption ก่อน expense, allowance, taxable และ PIT; ต้องจับ implementation ที่หักท้ายสูตรผิดได้ |
| C02-AC05 | RMF ใช้ร่วม PVD และ retirement inventory | baseline ลดภาษีจริง; capacity ลดครั้งเดียว; ไม่ให้ positive unsupported/unknown หลุด READY |
| C02-AC06 | Thai ESG ปี 2569 และยอดถือครองต่างปี | ซื้อปีปัจจุบันที่เข้าเงื่อนไขเท่านั้นมีผล; shared pool ตรงกฎและไม่ปะปน LTF transfer |
| C02-AC07 | ก่อน/ตรง/เกิน percentage cap, individual cap, shared cap | ยอดจ่าย/เข้าเกณฑ์/ใช้จริง/ส่วนเกิน reconcile; เพดานไม่ติดลบและไม่เกิด implicit optimization |
| C02-AC08 | สิทธิเดิมร่วมกับ incremental candidate เดิมที่รองรับ | baseline คำนวณสิทธิครั้งเดียว; saving เทียบ baseline นี้; เงินจ่ายเก่าไม่หักจาก budget ใหม่อีก |
| C02-AC09 | caller usage/snapshot ต่าง facts, ปี, hash หรือ version | ปฏิเสธข้อมูลที่ไม่ตรง authoritative replay; ไม่ให้ capacity ที่ใช้ฐานคนละชุด |
| C02-AC10 | core → discovery → candidates → HTTP/UI/export | ทุก consumer ใช้ readiness และผลตรงกัน; เมื่อข้อมูลกลับไม่ครบต้องไม่มีผลเก่าหรือ export หลุด |
| C02-AC11 | replay/version และ released assets | version ใหม่สำหรับ output/rule ที่เปลี่ยน; ของเก่า byte-for-byte; current engine ปฏิเสธ snapshot เก่าและ historical replay เลือก artifact ชัด |
| C02-AC12 | supported golden cases ของแต่ละประเภท | hand calculation อิสระพร้อม rule/แหล่ง/ปี/ขั้นตอน ไม่สร้าง expected ด้วย implementation เดียวกัน; exact Money/Decimal และ deterministic hash |

เพิ่ม fixture ตัวเลขพร้อมเอกสารคำนวณอิสระหลัง legal gate; ตารางนี้ยังไม่ใช่
หลักฐานว่าผ่าน acceptance. Regression เดิมทั้งหมดต้องผ่าน และ core coverage 100%

## 6. Evidence gate — ยังไม่ผ่านสำหรับ C02

วันที่ตรวจหน้าแหล่งต่อไปนี้: 2026-10-15. เป็น source reconnaissance สำหรับร่าง
ยังไม่ใช่การอนุมัติกฎปี 2569 และยังไม่มี raw-file hash ที่จัดเก็บสำหรับ C02

| Source | จุดอ้างอิง/สิ่งที่ตรวจพบ | ข้อจำกัด/งานที่ต้องทำต่อ |
| --- | --- | --- |
| [RD Clear Cut](https://www.rd.go.th/62777.html) | หัวข้อกองทุนสำรองเลี้ยงชีพ Q1 และ RMF Q1 แสดงการแยก allowance/exemption และวงเงินร่วม | FAQ ไม่พอเป็น authority สุดท้าย; ต้องตามกฎหมายและ amendment ที่มีผลปี 2569 |
| [RD ภ.ง.ด.90 ปี 2568 instructions](https://www.rd.go.th/fileadmin/tax_pdf/pit/2568/Ins90_241268.pdf) | คู่มือปีเก่าสำหรับตามรอยลำดับ/ประกาศ โดยเฉพาะหัวข้อ 10 RMF | ไม่ใช่คู่มือปี 2569; ห้ามนำมา certify ปีใหม่โดยไม่ตรวจ effective dates |
| [SEC ข่าว 170/2567](https://www.sec.or.th/TH/Pages/News_Detail.aspx?SECID=11027) | ย่อหน้า tax benefit ระบุช่วงซื้อ Thai ESG ถึง 31 ธ.ค.2569 | ต้องตาม ministerial regulation/amendments และปฏิสัมพันธ์ Thai ESGX ก่อนเพิ่ม treatment |
| [SEC Thai ESGX Q&A](https://www.sec.or.th/TH/Documents/Thai%20ESGX/QA-LTF-to-Thai%20ESGX-010468.pdf) | หน้า 1 ตารางและหน้า 2 ข้อ 4 เป็นจุดตั้งต้น shared pool ที่ตรวจใน C01 | เป็นหลักฐานเดิมของ C01; C02 ต้องตรวจข้อความ/กฎหมายล่าสุดและเก็บ artifact ของตนเอง |
| [RD FAQ RMF เก่า](https://www.rd.go.th/36195.html) | พบกฎเก่าที่ใช้ฐาน percentage/ขั้นต่ำต่างจากแหล่งใหม่ | **REJECTED เป็นหลักฐานกฎปัจจุบัน**; เก็บหมายเหตุเพื่อไม่หยิบกลับมาใช้ซ้ำ |

ก่อน implementation ต้องจัด evidence matrix ราย rule: URL, หน้า/มาตรา/ข้อ,
effective period, applicability ปี 2569, ข้อความที่รองรับ rule นั้น,
วันที่ตรวจและ hash ถ้าดึงไฟล์ได้ รวมประกาศ 401/414 และ amendment ที่เกี่ยวข้อง
ต้องตรวจเป็น chain ไม่ถือว่าการพบเลขประกาศคือการอ่าน/ยืนยันกฎหมายครบแล้ว
ถ้าข้อใดยืนยันไม่ได้ให้รายงานและ fail closed ไม่เดาหรือเพิ่ม rule จาก FAQ ล้วน

## 7. Release / งานที่ยังไม่ทำ

- [x] ร่าง scope, anti-double-count contracts, acceptance IDs และ evidence gaps
- [x] ผู้ใช้อนุมัติ scope/behavior ตาม review brief และ v0.1; DEC-019
- [ ] ปิดรายละเอียด treatment/readiness หลัง evidence review และบันทึก DEC ก่อน implementation
- [ ] ปิด legal evidence gate และจัด independent numeric fixtures
- [ ] เขียน implementation plan ผูก AC IDs, version migration และ tasks
- [ ] RED → GREEN, full gates, fresh review, mark progress และ acceptance record

ดู [progress ledger](../implementation-reports/TGPS-C02-progress.md).
ยังไม่มี implementation plan เพราะ evidence gate ยังไม่ผ่าน; ห้ามสร้างสถานะ PLANNED
ให้ดูเหมือนข้าม legal/review gate แล้ว และห้ามเริ่ม product code จากร่างนี้

## Change log

| Date | Version | Change | Basis |
| --- | --- | --- | --- |
| 2026-10-15 | 0.1-draft | ร่างสิทธิเดิม/unknown/capacity/version/AC/evidence gaps; ไม่เพิ่ม treatment | ผู้ใช้ให้ทำงานรับช่วงและร่าง C02 ต่อ; DEC-015 |
| 2026-10-21 | 0.1 | ผู้ใช้อนุมัติ scope/behavior หลัง review brief และสั่งทำ evidence/fixtures ต่อ; legal gate ยัง OPEN, ไม่เริ่ม treatment | DEC-019 |
| 2026-10-22 | 0.1 (linked UX draft) | เพิ่ม [แบบ UX สำหรับรีวิว](TGPS-C02-guided-rights-ux.md) ตามเป้าหมายอ่านง่าย; รายละเอียดหน้าจอยัง AUTHORING_DETAIL ไม่เปลี่ยนสัญญา/อนุมัติ implementation | DEC-020 |
| 2026-10-22 | 0.1 (UX approved) | ผู้ใช้อนุมัติแบบ UX; ทำ standalone prototypeในdocsและfield/copy inventory ไม่เปลี่ยนtax/HTTP contractหรือปิดlegal gate | DEC-021 |
| 2026-10-22 | 0.1 (staging proposed) | เพิ่ม [C02A proposal](TGPS-C02A-pvd-first-slice.md) แยกสำหรับscope review; parentapprovedscopeยังไม่เปลี่ยน | DEC-022 AUTHORING_DETAIL |
| 2026-10-22 | 0.1 (staging approved) | C02A scope approved; bounded evidence เพียงพอสำหรับ planning ของ normal PVD เท่านั้น; แผน4tasksรอรีวิว ไม่ปิด parent legal gates รวม | DEC-023 / DEC-024 |
