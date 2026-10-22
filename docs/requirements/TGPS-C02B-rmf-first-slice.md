# TGPS-C02B — RMF ซื้อครั้งแรก โดยไม่มีสิทธิเกษียณอื่นร่วม

Version: `0.1` · Date: `2026-10-22` (Asia/Bangkok)
Status: **REQUIREMENT_REVIEW — staged scope APPROVED (DEC-028); scoped evidence/contract review OPEN**
Implementation: **NOT_STARTED** · Implementation plan: **DRAFT_FOR_REVIEW** ([4 tasks](../superpowers/plans/2026-10-22-c02b-first-rmf.md))
Parent: [C02 v0.1](TGPS-C02-existing-rights.md)
Evidence: [RMF facts/time packet](../policy-evidence/2026-10-22/rmf-facts-review/README.md)

## เป้าหมายและเหตุผล

เพิ่มสิทธิจากเงินซื้อ RMF ที่จ่ายจริงแล้วให้ baseline ภาษีของพนักงานเงินเดือน
40(1) ปี2569 โดยเริ่มกรณีที่ตรวจแยกได้ก่อน กรณี RMF ร่วม PVD ยังติดการตีความ
ฐาน percentage cap ซึ่งให้ภาษีต่างกันตาม diagnostic เดิม จึงไม่เลือกสูตรเงียบ ๆ

นี่เป็นข้อเสนอของ agent หลังผู้ใช้สั่งเดินงานต่อ ไม่อ้างว่าผู้ใช้อนุมัติการจำกัด
READY coverage นี้แล้ว และไม่ข้าม legal gate ด้วยการลดขอบเขตเพียงอย่างเดียว

## ทางเลือกที่พิจารณา

| ทางเลือก | ข้อดี | ข้อจำกัด |
| --- | --- | --- |
| เริ่ม RMF ซื้อครั้งแรก ไม่มี PVD/สิทธิเกษียณอื่นร่วม (ข้อเสนอ) | ตรวจการซื้อ การแจ้งใช้สิทธิ และเพดานของประเภทเดียวได้ โดยไม่เลือกคำตอบของ combined-PVD | ยังใช้ RMF ร่วม PVD หรือประวัติกองทุนเดิมไม่ได้; ต้องอนุมัติ staged scope และ scoped evidence ก่อน |
| รองรับ RMF ร่วม PVD ในคราวเดียว | ครอบคลุมพนักงานที่มี PVD อยู่แล้ว | ต้องปิด G3/G4 โดยตรงก่อนเขียนแผน; ยังไม่มีหลักฐานเพียงพอให้เลือกสูตร |

ยังไม่มีคำตอบเลือกแนวทางจากผู้ใช้ในขณะจัดร่าง การอนุมัติ parent เดิมไม่เท่ากับ
การอนุมัติข้อจำกัดใหม่ในร่างนี้

## ขอบเขตที่เสนอ

- เงินเดือน40(1) ปี2569 และ baseline coverage เดิมครบ ไม่มีข้อยกเว้นเงินได้อื่น
  ที่ยังไม่รองรับ; ใช้รายได้ทั้งปีที่ผู้ใช้ระบุตาม contract เดิม ไม่เพิ่ม forecast
- ซื้อ RMF ด้วยเงินของผู้มีเงินได้เองเป็นครั้งแรกในปี2569 ไม่มีประวัติซื้อ/ใช้สิทธิ
  RMF ก่อนปีนี้; ระบุข้อเท็จจริงนี้เอง ไม่อนุมานจากช่องประวัติว่าง
- เริ่มหนึ่งกองทุนปกติ/หนึ่ง บลจ.; ซื้อหลายครั้งในปีเดียวกันได้เมื่อรวมยอดซื้อจริง
  ที่มีหลักฐานแล้ว ไม่อาศัยลำดับ input เพื่อเลือกภาษี
- ต้องยืนยัน PVD และสิทธิเกษียณประเภทอื่นเป็นศูนย์/ไม่มีตาม inventory จริง
  รวมถึง Thai ESG/ESGX และสิทธิสืบเนื่องที่ยังไม่รองรับ; ไม่ใช้ default zero
- ไม่รับ RMF for PVD, หน่วยที่รับโอน, การสับเปลี่ยน/ขาย/ไถ่ถอน/รับประโยชน์/
  การกู้หรือเบิกจากกองทุน และกรณีแก้สิทธิย้อนหลังใน slice นี้
- ต้องระบุประเภทสิทธิตามหลักฐานการซื้อ ไม่ตัดสินจากคำว่า RMF ในชื่อกองทุน
- เงื่อนไขการซื้อที่จ่ายแล้ว การแจ้งใช้สิทธิ และประวัติต้องครบใน coverage ที่รีวิว
  ไม่รับยอด arbitrary usage มาแทน facts

PVD-positive/RMF-zero ที่รองรับใน C02A ต้องยังใช้ได้เหมือนเดิมเมื่อข้อมูลครบ
ทั้งสอง positive ยังปิดผลพร้อมบอกว่า “ยังไม่รองรับ RMF ร่วม PVD” จนมีงานแยก
zero ทั้งสองยังรักษาพฤติกรรมเดิม ไม่มีการเพิ่มข้อห้ามให้โปรไฟล์ที่ไม่มี RMF

## ข้อมูลปัจจุบันกับเงื่อนไขอนาคต

ข้อเสนอสำหรับ review นี้ต้องแยกสามเรื่อง:

1. **ข้อเท็จจริงที่ตรวจได้แล้ว:** ยอดซื้อจริง ปี/ประเภทการซื้อ ซื้อครั้งแรก
   ไม่มีเหตุออกนอก coverage และได้แจ้งความประสงค์ใช้สิทธิต่อ บลจ.แล้วหรือยัง
2. **เงื่อนไขในอนาคต:** การถือครองและการขายคืน ต้องบอกเป็นภาระต่อเนื่องตามกฎ
   ไม่ให้ผู้ใช้ตอบว่าเหตุการณ์อนาคต “ผ่านแล้ว” และไม่อ้างว่าระบบตรวจอนาคตได้
3. **การส่งข้อมูลของ บลจ.:** แยกจากการแจ้งใช้สิทธิของผู้ซื้อ สถานะยังไม่ถึงกำหนด
   ไม่เท่ากับส่งแล้วหรือผิดเงื่อนไข; กรณีขัดแย้ง/แก้ข้อมูลต้องมี route ที่รีวิวก่อน

ต้องรีวิวหลักฐานและถ้อยคำว่า “ประมาณการภายใต้เงื่อนไขการถือครองต่อเนื่อง” ก่อน
เปิดผลตัวเลข ไม่ลดความหมายของ READY โดยซ่อนเงื่อนไขสำคัญในรายละเอียด
การรับทราบเงื่อนไขไม่ใช่หลักฐานว่าการปฏิบัติในอนาคตเกิดขึ้นแล้ว
เอกสารนี้ยังไม่อนุมัติว่ากรณี reporting pending ใดควร READY

## ผลคำนวณและการปิดผลที่เสนอ

- เมื่อ facts และ scoped legal contract ผ่านครบ ให้แสดงยอดจ่าย ยอดเข้าเกณฑ์
  ยอดใช้สิทธิ และส่วนเกิน แยกกัน พร้อม trace/provenance ของ version ที่ใช้
- จำนวน percentage/type cap และลำดับหลัง expenses ต้องมาจาก pack ใหม่หลังรีวิว
  ไม่ hardcode ใน adapter/JS และไม่แก้ pack/catalog ที่ออกแล้ว
- Positive RMF ขั้นแรกเปิด baseline/breakdown เท่านั้น เช่น C02A ไม่เปิด
  ทดลองใช้เงินเพิ่ม/capacity/candidates/saving จนมี requirement รองรับ consumer
  ที่เกี่ยวข้องครบ; domain ตัดสิน availability ไม่ใช่หน้าเว็บ
- Unknown → REQUIRES_INPUT; กรณีสำคัญนอก coverage → named UNSUPPORTED/
  ADVANCED ตาม precedence เดิม ปิด PIT/taxable/saving/candidates/export ทั้งหมด
- Baseline READY จึง export baseline ที่ตรง facts/hash ได้ พร้อมเงื่อนไขและ scope
  ไม่ปนผลแผนใช้เงินเก่าหรือยอดประหยัดที่ไม่ได้คำนวณ
- ไม่แนะนำผลิตภัณฑ์ ไม่จัดอันดับ ไม่คำนวณผลตอบแทน ไม่เพิ่ม storage/network/runtime
  dependency หรือ model ที่เติมคำตอบภาษีแทนผู้ใช้

## Acceptance cases สำหรับแผนภายหลัง

| ID | กรณี / สิ่งที่ต้องตรวจ |
| --- | --- |
| C02B-AC01 | unknown เทียบ zero ของยอดซื้อ/inventory/ประวัติ; ไม่อนุมาน first-ever/ไม่มีสิทธิจาก absence |
| C02B-AC02 | positive normal first purchase, declaration known; ชื่อกองทุนอย่างเดียวไม่พิสูจน์ classification |
| C02B-AC03 | PVD-positive/RMF-zero รักษา C02A; bothpositive ปิดผลพร้อมชื่อเหตุ; RMFzero ไม่เพิ่มข้อจำกัดใหม่ |
| C02B-AC04 | ก่อน/ตรง/เกิน percentage และ individual cap; bought/qualifying/claimed/excess reconcile ด้วย fixture อิสระ |
| C02B-AC05 | historical RMF, transfer, disposal, benefits/borrowing, multi-fund/AMC และ unknown eligibility ปิดผลตาม coverage |
| C02B-AC06 | declaration unknown/false และ manager report not-yet-due/unknown/discrepant ต้องแยกกันตาม contract ที่รีวิว; ห้าม default completed |
| C02B-AC07 | เงื่อนไขถือครองในอนาคตแสดงชัด; ไม่อ้าง future compliance หรือบังคับตอบเหตุการณ์อนาคตว่าเกิดแล้ว |
| C02B-AC08 | positive RMF baseline-only ผ่าน core→consumer→HTTP/UI/export; แก้ข้อมูล/late response ไม่คืนผลเก่า |
| C02B-AC09 | version/hash/replay แยก current/historical และ original artifacts byte-for-byte |
| C02B-AC10 | independent rule/numeric review, RED→GREEN, full gates/coverage100%, responsive/keyboard/reduced-motion QA และ acceptance แยกจาก tests |

## Gate ก่อนเขียน implementation plan

- [x] ผู้ใช้อนุมัติ staged scope นี้และ baseline-only availability โดย DEC-028
- [ ] Scoped amendment/current-applicability review ของ MR126/MR357/DG401/DG414
- [ ] ยืนยัน ordinary RMF legal classification/own purchase และ first-ever facts
- [ ] ตกลง fact/time/readiness contract โดยเฉพาะ reporting pending และ future obligations
- [ ] independent fixtures สำหรับ single-type percentage/cap/order พร้อม review record
- [ ] ถ้าได้ข้อยุติครบจึงปรับ requirement/DEC และเขียน plan ผูก acceptance IDs

การอนุมัติขอบเขตไม่ปิด legal gates อัตโนมัติ Parent C02 G1–G6 ไม่ถูกปิดรวม
C02A reduced-motion/user acceptance และ C01/F09 คงสถานะเดิม ไม่ merge/release

## Builder review

Fresh read-only reviewer `c02b_builder_check`: **nothing important left for scope
review**. ยังไม่พร้อม implementation plan จนปิด scope approval, scoped legal
applicability, fact/time/readiness และ independent-fixture gates ข้างต้น
เป็นการตรวจความชัดของเอกสาร ไม่ใช่ legal certification หรือ user approval
ดู [progress ledger](../implementation-reports/TGPS-C02B-progress.md)

## Change log

| Date | Version | Change |
| --- | --- | --- |
| 2026-10-22 | 0.1-draft | เสนอ first-purchase RMF-only staged scope และ review gates; ยังไม่อนุมัติ ไม่มี plan/product edits |

## Scope approval follow-up

ผู้ใช้อนุมัติ staged scope ตาม DEC-028 แล้วตั้งแต่คำตอบล่าสุด ข้อความเสนอ/ยังไม่มี
คำตอบข้างบนเป็นประวัติขณะจัดร่าง ไม่ใช่การขอ scope approval ซ้ำ
Scoped evidence/contract/fixtures และ implementation plan ยังไม่อนุมัติ

| Date | Version | Change |
| --- | --- | --- |
| 2026-10-22 | 0.1 | ผู้ใช้อนุมัติ first-purchase RMF-only scope และ baseline-only; DEC-028. ยังต้อง scoped evidence/contract review ก่อน plan |

## Detailed contract สำหรับรีวิวแผน

เป็นรายละเอียดทางวิศวกรรมจาก scoped evidence review ไม่อ้างว่า DG414 กำหนด
enum หรือ READY ของซอฟต์แวร์ และยังไม่อนุมัติให้เปิด treatment ใน runtime

- `other_rights.rmf=false` ที่ผู้ใช้ยืนยันคือไม่มีซื้อ RMF ในปีนี้ จึงไม่ต้องถาม
  รายละเอียด RMF เพิ่มเมื่อไม่เกี่ยวข้อง; inventory/history เดิมที่จำเป็นยังต้องครบ
  ไม่มีการสร้างคำตอบ eligibility/history อัตโนมัติ `None` ยังคง missing
- ถ้า presence=true ต้องมี own paid >0 และรายละเอียดครบ; falseพร้อมยอดบวก
  หรือ trueพร้อมยอด0เป็นข้อมูลขัดกัน มี private field error ไม่เลือกคำตอบแทน
- ต้องมีวันซื้อครั้งแรกและวันที่ประเมินที่ผู้ใช้ส่งจริงในปี2569 และวันซื้อ≤วันประเมิน
  ยอดซื้อสะสมยืนยันว่าเป็นยอดจ่ายจริงถึงวันประเมิน ไม่ใช้ clock หรือเงินตั้งใจซื้อ
- ยืนยันจากหลักฐานว่าเป็น ordinary own RMF purchase, หนึ่งกองทุน/หนึ่ง บลจ.,
  ซื้อเป็นครั้งแรกในปีนี้ ไม่มีโอน/ขาย/รับประโยชน์/กู้หรือเบิก และไม่มีสิทธิอื่นที่กระทบ
- ต้องแจ้งใช้สิทธิแล้ว: unknownเป็นmissing; ยังไม่ได้แจ้งเป็นnamedunsupported
  ของ route ปัจจุบัน ไม่ใช่คำตัดสินว่าหมดสิทธิทางกฎหมายถาวร
- `reporting_status` เป็น explicit NOT_YET_DUE / CONFIRMED_SUBMITTED /
  DISCREPANCY_OR_CORRECTION หรือNone(unknown). NOT_YET_DUE ต้องก่อนกำหนดปกติ
  จากpackและมีคำตอบยืนยันว่าไม่มีปัญหารายงานที่ทราบอยู่; ไม่อนุมานสถานะนี้จากช่องว่าง
- CONFIRMED_SUBMITTED ต้องมี snapshot ชื่อกองทุน/บลจ./ปี/ยอดซื้อสะสม/วันที่ยืนยัน
  ตรงfactsปัจจุบัน; วันซื้อ≤วันยืนยัน≤วันประเมิน. แก้ยอด/กองทุน/บลจ.ต้องล้าง
  confirmationบนUI และdomainปฏิเสธsnapshotไม่ตรงโดยอิสระ. ไม่ตรวจระบบ บลจ.ออนไลน์
- กรณีมีปัญหารายงาน/ต้องแก้ไขยังunsupportedพร้อมระบุกรณี ไม่ตัดสินภาษีย้อนหลัง;
  filingปี2570และข้อยกเว้นกำหนดเวลายังอยู่นอกsliceการประเมินในปี2569นี้
- การรับทราบภาระในอนาคตจำเป็นต่อ conditional-estimate route; unknownขอinput,
  ไม่รับทราบยังunsupportedในrouteนี้ ไม่ใช่หลักฐานว่าซื้อผิดกฎหมาย. แสดงภาระ
  การซื้อต่อเนื่อง ถือครอง/ขายคืน ไม่รับเงินระหว่างลงทุน และไม่กู้/เบิก ตามpack
- positiveRMF READY ต้องเห็นคำว่า **ประมาณการภายใต้เงื่อนไข RMF ที่ต้องปฏิบัติต่อเนื่อง**
  ทั้งsummary/detail/export; conditionsและreporting noticeเป็นmaterial/hash
  ไม่แสดงว่าอนาคตผ่านแล้ว ไม่เปิดnew-cash/capacity/candidates/tax_impact/saving
- Ordinary RMF cap/order สำหรับsingle-typeนี้มี13referencecasesตรวจสองวิธีตรงกัน;
  exact-derivedprecisionคงตามcoreเดิม ไม่อ้างเป็นfilingrounding. ยังไม่ใช้สูตร
  RMFร่วมPVDหรือร่วมสิทธิเกษียณอื่น และไม่เรียกparent C02ว่าจบ

Scoped evidence disposition: **ADEQUATE_FOR_PLANNING_ONLY** ตาม independent
reviewและrulingsใน[bounded packet](../policy-evidence/2026-10-22/c02b-scope/README.md).
รายละเอียดนี้ต้องอยู่ในแผนที่ส่งรีวิวก่อนimplementation ไม่ถามscopeDEC-028ซ้ำ

| Date | Version | Change |
| --- | --- | --- |
| 2026-10-22 | 0.1 planning detail | Scoped evidence/independent arithmetic13/13 adequate for planning only; add explicit proposed fact/time/reporting snapshot contract and draft4task plan, pending user plan/contract review |
