# C02A — เริ่มคำนวณ PVD กรณีพื้นฐานก่อน

Version: `0.1` · Date: `2026-10-22` (Asia/Bangkok)
Detailed requirement: **AGREED_DIRECTION — staged scope approved; evidence ADEQUATE_FOR_PLANNING_ONLY**
Implementation: **IN_PROGRESS** (DEC-025; Native execution)
Parent: [C02 v0.1](TGPS-C02-existing-rights.md); staging approved under DEC-023 after DEC-022 proposal

## 1. ข้อเสนอที่ขอให้ตัดสินใจ

เริ่มเชื่อมการคำนวณจริงกับหน้าจอที่อนุมัติแล้ว **เฉพาะ PVD พนักงานนายจ้างเดียว
อัตราปกติ** ก่อน โดยเปิดภาพรวมภาษีและที่มาของสิทธิPVD;
การทดลองใช้เงินใหม่ในโปรไฟล์ที่มีPVDยังไม่เปิดในsliceนี้.
RMF/ThaiESGยังเป็นงานC02ขั้นถัดไป; ไม่ได้ตัดออกจากroadmap.
กรณีที่ยังไม่รองรับต้องบอกชื่อและปิดผล ไม่ถือว่าไม่มีเพื่อลัดให้คำนวณผ่าน.

เหตุผล: มีหลักฐานตรงสำหรับ split/expense-order/normal-rate PVDแล้ว แต่การรวม
หลายนายจ้างและฐานRMFยังไม่ผ่านreviewครบ. การลดขอบเขตREADYครั้งแรกจึงต้อง
อนุมัติอย่างชัดเจน ไม่อนุมานจากคำสั่งให้ค้นกฎหมายต่อ. Parentยังไม่ผ่านlegalgate
และจะไม่ถูกเลื่อนเป็นIMPLEMENTEDเมื่อทำC02Aเสร็จ.

## 2. Supported coverage ที่เสนอ

| กรณี | การจัดการในC02Aที่เสนอ |
| --- | --- |
| เงินเดือน40(1), ปี2569, นายจ้างเดียวตลอดปี ไม่มีเปลี่ยนงาน/หลายกองทุน | ตรวจสิทธิPVDตามข้อมูลครบ; baselineอื่นต้องผ่านcoverageเดิมด้วย |
| เงินสะสมลูกจ้างจริงจากPVDจดทะเบียน อัตราปกติตามข้อบังคับกองทุน | ใช้ยอดลูกจ้าง; เงินนายจ้างไม่เพิ่มสิทธิลดหย่อน |
| ฐานค่าจ้างตามกฎหมายกองทุนระบุชัด | ไม่ใช้รายได้รวมแทนโดยอัตโนมัติ; ผลรวมฐานต้องไม่เกินรายได้จากการจ้างงานที่ระบุ |
| ยอดจ่ายเกิน500000แต่ยังอยู่ในอัตราปกติและฐานที่ยืนยัน | จำกัดสิทธิPVDและแสดงส่วนเกิน; ไม่มีRMF/สิทธิอื่นให้เลือกจัดสรรในsliceนี้ |
| RMF/ThaiESG/ESGX/สิทธิเกษียณอื่นในปีนี้ | ต้องยืนยันexplicitzeroเป็นรายประเภทตามinventory; positiveยังUNSUPPORTEDและปิดผล |
| หลายนายจ้าง/เปลี่ยนงาน/หลายกองทุน/อัตราสะสมพิเศษ | UNSUPPORTEDพร้อมระบุกรณี ไม่clipเข้าnormalpath |
| ขาย/ถอน/โอนกองทุน/เกษียณ/recapture/สิทธิสืบเนื่องLTFในปีนี้ | UNSUPPORTEDหรือADVANCEDตามdomainที่เกี่ยวข้อง; ไม่คำนวณบางส่วนแล้วแสดงPIT |
| เคยใช้สิทธิRMFหรือสิทธิอื่นที่มีเงื่อนไขต่อเนื่อง ซึ่งยังต้องตรวจประวัติ | ยังไม่รองรับในsliceนี้; ไม่ใช้ยอดซื้อใหม่0แทนการยืนยันประวัติ |
| ไม่รู้ยอด/ฐานค่าจ้าง/อัตรา/ข้อมูลนายจ้าง/การจดทะเบียน/สิทธิอื่นที่กระทบผล | REQUIRES_INPUTตามdomain; ไม่เติม0/eligibleให้เอง |

การไม่ทราบหรือunsupportedต้องใช้precedenceเดิมทั้งcore/UI/discovery/candidates/export.
“ไม่มีเงินสะสมใหม่”ไม่ยืนยันว่าไม่มีขาย/โอน/สิทธิปีก่อน; ใช้UXที่อนุมัติไว้.
ข้อจำกัดนายจ้างเดียว/กองทุนเดียว/อัตราปกติใช้เฉพาะเมื่อpositivePVD.
PVD=0ที่ผู้ใช้ยืนยันและไม่มีเหตุอื่นที่กระทบผลยังใช้supportedcoverageเดิม;
ไม่เพิ่มข้อห้ามหลายนายจ้างให้โปรไฟล์ที่ไม่มีPVD. Factsสิทธิ/ประวัติที่เกี่ยวข้อง
ยังต้องครบตามcontract ไม่อนุมานzeroจากabsenceของschemaเก่า;
currentengineไม่รับsnapshotเก่าเป็นผลปัจจุบันตามversionboundaryเดิม.
กรณีข้อมูลขัดกัน เช่น positivepaidแต่wage0 หรือbasisเกินsalary ให้errorข้อมูล
โดยระบุชื่อฟิลด์ ไม่echoยอด. ไม่ยกระดับเป็นREADYจากข้อมูลที่ขัดกัน.

## 3. การคำนวณที่เสนอให้ผ่านreviewก่อนลงโค้ด

สำหรับpositivePVDในnormalcoverageข้างบนเท่านั้น:

`salary/section_40_1`ต้องเป็นเงินได้จากการจ้างงานทั้งปี **ก่อนหักexemptionPVD**;
ไม่รับยอดที่ผู้ใช้หักPVDไปแล้วมาหักซ้ำ. ช่องกรอกใช้คำอธิบาย
“ยอดรายได้ก่อนหักเงินสะสม PVD และสิทธิลดหย่อน” และแยกฐานค่าจ้างPVDอีกช่อง.

1. ใช้employee paidที่ยืนยันว่าตรงข้อบังคับอัตราปกติ2–15%ของฐานค่าจ้าง;
   annual paidต้องอยู่ในช่วงนี้ของฐานที่เป็นช่วงจ่ายเงินสะสมจริง.
   ถ้าannualratioอยู่นอกช่วง หรือไม่อาจยืนยันว่าไม่มีministerialexception/
   การจ่ายสะสมไม่ปกติ ให้ปิดผล ไม่ลดpaidลงให้ดูเป็นอัตราปกติ.
2. PVDallowance = min(employee paid,10000).
3. PVDexemption = min(max(employee paid−10000,0),490000).
4. หักexemptionจากincomeก่อนemploymentexpense;
   หักallowanceหลังexpenseพร้อมสิทธิbaselineเดิมที่รองรับ.
5. ยอดPVDใช้สิทธิ = allowance+exemption; ส่วนเกิน = paid−ยอดใช้สิทธิ.
   เก็บprovenanceและยอดในauthoritativebaselineชุดเดียว; consumerไม่หักซ้ำ.

ตัวเลข/ลำดับผูก Code47(1)(ช), MR126§2(35)/MR266§1, Code42ทวิ,
PND91formที่เก็บไว้PDF2ก1–7/ข1และPDF3deduction8; normal-rateนิยามจาก
PVDAct§§3,5,6,9,10. แหล่ง/วันที่/ข้อจำกัดใน
[evidence](../policy-evidence/2026-10-21/README.md) และ
[PVDfollow-up](../policy-evidence/2026-10-21/pvd-follow-up/README.md).
การอนุมัติscopeไม่แทนการตรวจamendment/current-applicability/independentfixtures.

Scoped review2026-10-22: [bounded evidence/qualifying-fund chain](../policy-evidence/2026-10-22/c02a-scope/README.md)
และ independent arithmetic9/9 เพียงพอสำหรับเขียนแผนของsliceนี้เท่านั้น.
เงินสะสมหมายถึงยอดลูกจ้างที่เข้ากองทุนจริงในปีภาษี แยกจากยอดหักpayroll;
ต้องยืนยันกองทุนจดทะเบียน ฐาน/ช่วงสะสม อัตราตามข้อบังคับ และการนำส่งปกติ.
การนำส่งล่าช้า/ผิดปกติ/พักหรือเลื่อนตามข้อยกเว้นอยู่นอกcoverageของslice
ไม่ใช่คำวินิจฉัยว่าลูกจ้างเสียสิทธิตามกฎหมายทุกกรณี; unknownที่จำเป็นปิดผล.
ไม่ถามให้รับรอง“ครบเงื่อนไขกฎหมายทั้งหมด” และไม่เรียกเอกสารอนุมัติรายจ่ายบริษัท.
คิดเฉพาะเงินสะสมของผู้มีเงินได้คนนี้ ไม่เปิดสิทธิจากคู่สมรสและไม่ห้ามผู้สมรสทั้งหมด.

ไม่ต้องตัดสินฐานRMFหรือการจัดสรรoversubscribedหลายสิทธิสำหรับsliceนี้;
positive/unknownที่เกี่ยวข้องยังปิดผล. “วงเงินเกษียณที่เหลือสำหรับRMF”ยังไม่แสดง
เป็นสิทธิที่พร้อมใช้ และไม่สร้างRMFcandidateจากการลบยอดPVDอย่างเดียว.

Consumerboundaryที่เสนอ: positivePVDที่baselineREADYแสดงPIT/taxableและ
PVDbreakdown/exportเฉพาะbaselineที่versionไว้ได้; discovery/การใช้เงินใหม่
แสดง“ยังไม่เปิดการทดลองเงินเพิ่มสำหรับกรณีที่มีPVD”พร้อมavailabilityreason
จากdomain ไม่สร้างcandidate/saving/capacityใดๆจากการคาดเดาฐานpercentage.
ห้ามแปลงการปิดส่วนทดลองเงินเป็นbaselineUNSUPPORTEDหรือเปลี่ยนstatusprecedence.
แผนภายหลังต้องกำหนดtypedavailability/consumercontractชัดก่อนimplement;
ถ้าbaselineไม่READYต้องปิดผลทั้งหมดตามกฎเดิม.

PVD=0และfactsอื่นผ่านcoverageเดิมให้คงdiscovery/candidatesเดิม.
SourceinspectionพบcatalogมีThaiESGnew-cashและretirement-shared-capacityright
แต่ไม่มีRMFnew-cashdefinitionปัจจุบัน; ไม่อ้างว่ามีRMFcandidateที่ต้องคงไว้.
การปิดnew-cashเฉพาะpositivePVDเป็นproposedstagingboundary ไม่ใช่การแก้catalogเก่า.

## 4. ข้อมูล/หน้าจอและinterface boundaries

- ใช้UXv0.1ที่อนุมัติ: มี/ไม่มี/ยังไม่ทราบ, เปิดฟิลด์เมื่อเกี่ยวข้อง,
  ประวัติกองทุนแยกจากเงินใหม่, errorพาไปฟิลด์, ผล3ระดับและauto450ms.
  ผู้ใช้ต้องเห็นข้อความว่าภาพรวมภาษีพร้อมแต่การทดลองเงินเพิ่มยังไม่เปิด;
  ไม่สร้างtabที่ดูพร้อมใช้แต่กดแล้วได้ตารางว่าง.
- เพิ่มtypedimmutablefactsสำหรับpaid/wage/rate/employer/fund/coverageที่ต้องใช้;
  `amount_used`/`shared_usage`เดิมไม่ใช่paidหรือeligibilityauthority.
- ยืนยันtaxyear, currentengine/pack/catalogและfactsเดียวกันทุกconsumer;
  snapshotsเก่าไม่ถูกยอมรับเป็นผลปัจจุบัน.
- rulepackใหม่และengine/consumerversionใหม่เมื่อผลเปลี่ยน; เก็บpackเดิม
  byte-for-byteและreplayต้องเลือกversion/hashชัดเจน.
- runtimeยังstandardlibrary, ไม่มีnetwork/clock/random/storageในcalculationpath.
  Previewในdocsไม่ใช่productimplementationและไม่ใช่ตัวตัดสินREADY.

## 5. Acceptance ที่เสนอ

| ID | กรณีที่ต้องพิสูจน์ |
| --- | --- |
| C02A-AC01 | unknownเทียบexplicitzeroของยอด/ฐาน/coverage; ไม่เกิดsilentdefaults |
| C02A-AC02 | positivePVDregistered/singleemployer/normalrateเท่านั้นเข้าsupportedpath; employercontributionไม่เพิ่มสิทธิ |
| C02A-AC03 | splitที่9999/10000/10001และ499999/500000/500001 พร้อมclaimed/excessreconcile |
| C02A-AC04 | lowwageจับexemptionก่อนexpenseจากtaxable ไม่ตรวจแค่PIT0 |
| C02A-AC05 | multijob/multifund/exceptionalrate/history/otherpositivesปิดผลและชื่อเหตุผลถูก; ไม่มีใหม่แต่มีhistoryไม่หลุด |
| C02A-AC06 | PVDpaidเดิมถูกคิดในbaselineครั้งเดียว ไม่หักจากbudgetใหม่ซ้ำ; positivePVDไม่มีnew-cashcandidate/saving/capacity; PVD=0คงbehaviorที่รองรับเดิม |
| C02A-AC07 | API/UI/export/discovery/candidatesตรงdomain; edit/late/errorไม่เผยผลเก่าหรือpartialtaxresult |
| C02A-AC08 | version/hash/replay/current-snapshotrejectionและold-artifactimmutabilityถูกต้อง |
| C02A-AC09 | full100%corebranch/statementcoverage, fresh-serverfrontend, narrow/mobile/keyboard/reduced-motionจริง |

## 6. Gates / ขั้นต่อไป

- [x] เขียนproposalที่ตรวจได้และแยกจากapprovedparent
- [x] ผู้ใช้อนุมัติstagedREADYcoverageนี้ด้วย “โอเครครับ ลุย!”; บันทึก DEC-023
- [x] ปิดevidence/independentfixture reviewเฉพาะnormalcoverageนี้สำหรับการวางแผน;
  รวมedgecasesและการไม่reuseauthorityผิดความหมาย
- [x] เขียน [AC-linked implementation plan](../superpowers/plans/2026-10-22-c02a-normal-pvd.md) และ self-review; DRAFT_FOR_REVIEW ยังไม่อนุมัติแผน/เลือกวิธี execution
- [ ] RED/GREEN → verify → freshreview → acceptance

ยังไม่ลงproductcode; แผนสร้างหลังscope approvedและscoped evidence reviewเพียงพอแล้ว.
ไม่เรียกC02ทั้งหมดว่าเสร็จ และไม่ถือว่าแผนได้รับอนุมัติจากการอนุมัติscopeก่อนหน้า.

## Builder review

`c02a_scope_check`พบ3คำถาม: ข้อจำกัดpositiveเทียบzeroPVD, grossincomeก่อนยกเว้น,
และexistingcandidates. แก้ข้อ2–4ให้ชัดตามข้างบน; ไม่ได้ปิดlegalreviewหรือถือว่า
userอนุมัติการปิดnew-cashสำหรับpositivePVD. Read-onlyreviewซ้ำ verdict
“nothing important left” สำหรับscopeapproval; legalreviewยังOPEN.

## Change log

| Date | Version | Change |
| --- | --- | --- |
| 2026-10-22 | 0.1 | ผู้ใช้อนุมัติ C02A staged scope ตาม DEC-023 หลังอ่านข้อเสนอ; scoped evidence review และ implementation ยังไม่เสร็จ บันทึก builder review ข้างบนเป็นประวัติก่อนอนุมัติ |
| 2026-10-22 | 0.1 (scoped evidence) | บันทึก chain/currency/actual-credit facts และ ordinary-employer reference9/9; ADEQUATE_FOR_PLANNING_ONLY ตาม independent review ไม่ใช่ legal certification หรือ product acceptance |
