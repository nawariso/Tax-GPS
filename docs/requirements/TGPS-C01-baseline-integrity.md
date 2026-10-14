# TGPS-C01 — Baseline Integrity & Supported Input Boundary

Version: `0.1`  
Created: `2026-10-15` (Asia/Bangkok)  
Scope: **AGREED_DIRECTION**  
Detailed requirement: **REQUIREMENT_REVIEW**  
Implementation: **IN_PROGRESS** (ดู [plan](../superpowers/plans/2026-10-15-c01-baseline-integrity.md) และ [ledger](../implementation-reports/TGPS-C01-progress.md))  
Priority: correctness before C02  
Jurisdiction/year: Thailand, 2026 / พ.ศ. 2569  
Initial taxpayer: Section 40(1) employment income

## 1. Intent และหลักฐานตั้งต้น

ทำให้ consumer ของ Tax GPS รู้ได้ตรงกันว่าฐานภาษีคำนวณได้ครบในขอบเขตที่รองรับ
หรือยังขาดข้อมูล/มีรายการที่ไม่รองรับ ห้ามเผย PIT และ incremental saving
แบบดูเหมือนผลพร้อมใช้เมื่อรายการที่มีผลต่อ baseline ถูกละไว้

Requirement นี้ต่อจาก [Product Review](../reviews/2026-10-15-product-domain-review.md)
และ [ข้อตกลง DEC-002](../DECISIONS.md#dec-002--งานแรกเป็น-baseline-integrity)
ฐานที่อ่านตอนจัดทำคือ `de85aee67e3da34e6a83c296ad88d6e377f0858a`
พร้อมรายงานรีวิวและสคริปต์สมมุติที่ยังเป็น working-tree additions
ไม่ถือว่ารายงานรีวิวเป็น commit ที่มีอยู่แล้ว

ข้อค้นพบที่ต้องปิด: F01 retirement, F02 shared usage, F03 unknown parent,
F04 source evidence และ F09 HTTP reliability
F05 เรื่อง coverage ของสิทธิพนักงานประเภทอื่นแก้ข้อความขอบเขตใน C01
แล้วเพิ่มการรองรับจริงใน C02

## 2. Goals, scope และขอบเขตงานต่อไป

### In scope

- สถานะและเหตุผลของ tax baseline ใน core, discovery, candidates และ local demo
- fail-closed สำหรับ material retirement, unsupported prior usage และ unknown eligibility
- explicit zero เทียบ unknown โดยไม่ใช้ truthiness กลืนค่า
- scope metadata และข้อความที่ไม่อ้างว่ารวมสิทธิพนักงานทั้งหมดแล้ว
- แก้ source provenance ผ่าน versioned artifacts และ deterministic replay
- ตรวจ HTTP failure ที่พบ พร้อมข้อสรุปที่มีหลักฐาน
- tests, migration notes และ implementation report ที่ผูกกับ requirement นี้

### งานในช่วงถัดไป

การเพิ่ม ledger/deduction จริงของ PVD, RMF, Thai ESG ที่ซื้อแล้ว, ประกันและสิทธิอื่น
อยู่ C02; forecast/withholding อยู่ C03; custom allocations และ action treatments
อยู่ C04; market projections/scenarios อยู่ C05; persistence อยู่ C06

C01 ไม่ใช้การหักยอด retirement หรือ shared usage ทั้งก้อนเป็นวิธีแก้
เพราะยังไม่มี eligibility และ treatment รายประเภทครบ
การบล็อกกรณีที่ยังไม่รองรับเป็นการปิดช่องว่างก่อนเพิ่มความสามารถใน C02

## 3. สัญญาที่คงใช้และส่วนที่เปลี่ยน

ใช้ pure Python domain, Money/Decimal, activated/versioned policy, explicit planning date,
progressive PIT และ financial guardrails เดิม
เก็บ NO_ACTION สำหรับ baseline ที่พร้อมและกรณีถูกจำกัดสภาพคล่องตามสัญญาเดิม

C01 อนุญาตการเปลี่ยนผลของ input ที่ระบุใน sections 4–6:
retirement/shared usage/unknown ที่เคยคืน READY อาจไม่เผยผลภาษีอีกต่อไป
ต้องปรับ fixtures และ consumers โดยบันทึกเหตุผล ไม่ลบ tests เพียงเพื่อให้ suite ผ่าน

C01 ไม่ยกเลิก independent acceptance pending ของ P1-004
และไม่เปลี่ยนสิทธิภาษีหรือ financial product policy โดยไม่มี evidence/review

## 4. Baseline readiness contract

เพิ่มหรือใช้สถานะที่มี semantics ดังต่อไปนี้; public serialized literals ของงานนี้คือ:

| Status | เงื่อนไข | PIT / taxable income / marginal rate | Additional tax impact |
| --- | --- | --- | --- |
| READY | known supported facts ครบ ไม่มี material unsupported inputs ตาม C01 | ตัวเลขจริง รวมศูนย์ที่ทราบ | ใช้ได้ตาม policy/capacity/guardrails |
| REQUIRES_INPUT | มี material unknown ตาม section 5 | null | ต้องถูกปิด |
| UNSUPPORTED | มี material positive benefit/usage ที่ยังไม่มี baseline treatment | null | ต้องถูกปิด |
| ADVANCED_TAX_PATH_REQUIRED | มี material unsupported income ตามสัญญาเดิม | null | ต้องถูกปิด |

READY หมายถึงพร้อม **เฉพาะ declared coverage** ของพนักงาน 40(1) และรายการที่ core รองรับ
ไม่ใช่ข้ออ้างว่าตรวจสิทธิทุกประเภท เอกสาร หรือภาษีจริงครบแล้ว

ทุก state ต้องมี machine-readable reasons, missing fact IDs เมื่อเกี่ยวข้อง,
engine version, policy identity และ output hash
scope/readiness/reasons เป็น material output ที่รวมในการ hashing/replay
การเรียก `tax_impact` บน non-READY ต้องถูกปฏิเสธ แม้ caller จะสร้าง object
ที่มี taxable income ติดมาด้วยอย่างไม่สอดคล้อง

Reason semantics ขั้นต่ำ:

- `RETIREMENT_BASELINE_UNSUPPORTED`
- `PRIOR_SHARED_USAGE_BASELINE_UNSUPPORTED`
- `PARENT_ELIGIBILITY_REQUIRED`
- `SHARED_USAGE_REQUIRED`
- `UNSUPPORTED_INCOME` พร้อมประเภทเงินได้ตามสัญญาเดิม

input ที่ผิดรูปแบบ/จำนวนติดลบยังเป็น validation error ไม่แปลงเป็น tax estimate
เมื่อมีหลายเหตุผลให้ retain material reasons ทั้งหมดในลำดับคงที่:
unsupported income → retirement → prior shared usage → parent eligibility → shared usage unknown
เลือกสถานะตาม precedence:
ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY

## 5. Input semantics ที่ต้องตัดสินเหมือนกันทุกชั้น

| Input | Known zero / false | Positive / true | Unknown |
| --- | --- | --- | --- |
| Retirement contributions | จำนวนทุกรายการเป็นศูนย์ไม่เพิ่ม deduction และไม่บล็อก baseline | อย่างน้อยหนึ่งรายการเป็นบวก: UNSUPPORTED จนกว่าจะมี treatment ใน C02 | หาก adapter รับ unknown ต้องไม่แปลงเป็นศูนย์; ปิดการเผยผลพร้อมเหตุผล |
| Usage ของ Thai ESG 2026 pool ที่รองรับ | ศูนย์หรือ explicit complete empty list ใช้ salary baseline ได้ | ยอดบวก: UNSUPPORTED สำหรับ baseline จนมี ledger/treatment ใน C02 | null/ไม่ได้ตรวจ usage: REQUIRES_INPUT; ไม่สมมุติว่าไม่มีการซื้อเดิม |
| Parent eligibility | false เป็นไม่มีสิทธิรายการนั้น | true ใช้ allowance ตาม caller assertion และ policy เดิม | None: REQUIRES_INPUT; ไม่ตีความเป็น false |

`OpportunityFacts.shared_limit_usage=()` มีความหมายว่า explicit complete list ไม่มี usage
ตาม semantics เดิมของ model; `None` ยังหมายถึงไม่ทราบ
ชื่อ pool ที่ระบบไม่รู้จักไม่สามารถให้ tax authority ได้ ต้อง reject ที่ boundary
หรือส่งสถานะไม่รองรับพร้อมเหตุผล ห้ามใช้ชื่ออื่นเพื่อเลี่ยงการตรวจยอดบวก
ให้ implementation plan เลือกหนึ่งพฤติกรรมสำหรับ unknown pool และใส่ contract test

กรณี legacy profile ที่ใช้ default shared usage = None จะเปลี่ยน readiness ตามตารางนี้
README/examples/fixtures ต้องกรอก explicit zero/no-records เมื่อเป็นข้อมูลสมมุติที่ทราบ
ห้ามให้ core เติมค่า default zero เพื่อรักษาตัวอย่างเก่าให้ผ่าน

สำหรับสิทธิที่ current core บังคับ known boolean เช่น personal/mortgage/child:
adapter ต้องคงการปิด unknown ไม่เติม true/false ให้อัตโนมัติ
ยังไม่เพิ่ม legal eligibility inference จากอายุ รายได้ เอกสาร หรือความสัมพันธ์ใน C01

## 6. Downstream และ UI behavior

- discovery ที่รับ non-READY tax state ต้องไม่เปิด allocatable opportunities
  และต้องรักษาเหตุผล/missing facts จาก baseline ให้ consumer อธิบายได้
- candidate activation/build ต้องปฏิเสธ non-READY อย่างชัดเจน
  ไม่สร้าง NO_ACTION ที่แสดง PIT 0 หรือ baseline เก่าทดแทนผลที่ไม่ทราบ
- non-READY baseline ปิดทั้ง PIT, incremental savings, comparisons และ result export
  ที่มีตัวเลขภาษีจากการคำนวณก่อนหน้า
- การแก้ input ต้อง invalidate ผลเก่า และ response เก่าต้องไม่เผยผลอีกครั้ง
- แสดงข้อความไทยที่บอก **รายการใด** ยังไม่รองรับหรือยังไม่ทราบ
  ห้ามใช้เพียง “ข้อมูลผิด” แล้วให้ผู้ใช้เดาว่าต้องแก้ช่องไหน
- positive shared usage ปิดเส้นทางเดโมทั้ง seven-field legacy และ extended profile
  โดยไม่เปลี่ยน usage เป็น zero หรือหักจาก income อย่างเงียบ
- unknown shared usage ปิดการเผย baseline ครบตาม C01; known zero ยังใช้เดโมได้
- ข้อความผล READY ใช้ความหมาย “รวมรายการที่รองรับและกรอกยืนยันแล้ว”
  พร้อมขอบเขต 40(1)/2026 และรายการที่ยังไม่รองรับ

ต้องรองรับเหตุผลแบบ machine-readable ที่ HTTP adapter ส่งได้
รูปแบบ error envelope/status code ที่ตรงกับ conventions เดิมเลือกใน implementation plan
แต่ tests ต้องตรวจ code และ missing field identity ไม่อิง prose เพียงอย่างเดียว
ไม่จำเป็นต้องเผย raw profile หรือ stack trace ใน error

## 7. Source evidence และ policy versioning

แก้ F04 โดยตรวจ source ของ Thai ESG ที่รองรับ rule semantics จริง
ระบุ title/publisher/publication date ที่ตรงกับต้นฉบับ, retrieved/verified dates,
rule IDs และ section/page ที่ใช้ยืนยัน cap/rate/holding/shared pool
ลิงก์ที่พบจากรีวิวเป็น candidate evidence ต้องอ่านและตรวจอีกครั้งตอนออก artifact:

- [SEC Q&A ชุดที่ 1](https://www.sec.or.th/TH/Documents/Thai%20ESGX/QA-LTF-to-Thai%20ESGX-010468.pdf)
- [Source URL เดิมใน catalog](https://www.sec.or.th/TH/Pages/News_Detail.aspx?SECID=11881&NewsNo=167&NewsYear=2568&Lang=TH)

สำหรับ SSO primary source แบบ index page ให้หา direct law reference/snapshot ที่ตรงกับ
rule หรือระบุ unresolved evidence และไม่อ้างว่า reverified แล้วเพียงเพราะ host เป็นทางการ
ถ้าสาระของ material production rule ยังยืนยันไม่ได้ ต้องคง DRAFT/ปิด activation
และรายงานข้อที่ยังขาด ห้ามเขียนวัน verified หรือ EFFECTIVE เพื่อให้ tests ผ่าน

runtime calculations ยัง offline/deterministic; การ fetch และ legal verification
เกิดในขั้นออก policy artifacts ไม่เกิดใน tax arithmetic
source evidence hash เป็นหลักฐานตรวจความเปลี่ยนแปลง ไม่ใช่ proof ว่ากฎหมายถูกต้อง

เมื่อ evidence/material semantics เปลี่ยน:

1. ออก artifact version ใหม่และปรับ engine versions ของ material consumers ที่ได้รับผล
2. ให้ current production selector เลือก version ที่ตรวจแล้วอย่าง explicit
3. เก็บ old artifacts และ explicit historical selection ด้วย version/hash
4. ห้ามใช้ historical selection อ้างความพร้อมของ current production rule
5. snapshots เก่าต้อง replay ด้วย matching historical engine/policy/catalog artifact
   หรือถูกปฏิเสธด้วย version mismatch ที่ชัดเจน ไม่ replay ด้วย current engine แล้วอ้างตรงกัน

ไม่จำเป็นต้องทำ compatibility engine ใหม่ทุกเวอร์ชัน
แต่ต้อง retain/refer old engine artifact และมี reproduction instructions ของ replay เก่า
การเปลี่ยน new default catalog ต้องปรับ candidate binding ให้รู้ version ที่ยอมรับจริง
โดยไม่ยอมรับ arbitrary caller catalogs

## 8. HTTP reliability investigation

F09 จากรีวิว: full suite รอบแรก failed ที่ POST Origin ไม่ผ่านด้วย WinError 10053
targeted rerun และ full suite รอบต่อมาผ่าน จึงยังไม่มี root cause ที่ยืนยันแล้ว

ต้องตรวจ request/response lifecycle โดยใช้ข้อมูลสมมุติ และบันทึก Windows/Python version,
คำสั่ง จำนวนรัน และผลเทียบ targeted/full-suite พร้อมกรณี Origin/Host/framing เดิม
จำนวนรันให้เลือกใน plan จากสมมุติฐานที่ตรวจ; ห้ามกล่าวว่า “แก้แล้ว” จาก rerun ผ่านอย่างเดียว

ถ้าพบ code defect ให้สร้าง regression ที่จับสาเหตุและแก้เฉพาะจุด
ถ้าหลักฐานชี้ environment/test harness ให้บันทึกการวินิจฉัยและวิธีลดผลกระทบ
ถ้ายังพิสูจน์ไม่ได้ ให้ issue มีสถานะ OPEN และ C01 acceptance ต้องระบุว่า conditional
หรือยังไม่ผ่าน ห้ามเงียบหรือข้าม test เพื่อให้ gate เขียว
ไม่เปลี่ยน loopback/Host/Origin/static allowlist หรือ body limits เพื่อหลีกเลี่ยง failure

## 9. Acceptance matrix

Golden inputs ที่เป็น READY ต้องระบุ explicit known zero shared usage
expected numbers ต้องคำนวณและตรวจโดยอิสระจาก engine ที่กำลังทดสอบ

| ID | Case | Expected |
| --- | --- | --- |
| C01-AC01 | เงินเดือน 990,500, SSO 10,500, personal eligible, no other supported rights, known zero usage | READY; taxable 820,000; PIT 79,000; extra eligible 100,000 saves 18,500 ตาม policy เดิม |
| C01-AC02 | เงินเดือน 300,000 กับ facts ที่ครบในขอบเขตเดิม | READY; taxable 129,500; PIT `0.00` ไม่ใช่ null |
| C01-AC03 | RMF/PVD/retirement category ใดมี amount > 0 | UNSUPPORTED จาก core; PIT/taxable/marginal null; reason retirement; tax impact/candidates ใช้ไม่ได้ |
| C01-AC04 | retirement records known zero | ไม่เพิ่ม deduction; supported salary result ไม่เปลี่ยน |
| C01-AC05 | supported shared usage = 100,000 | UNSUPPORTED; ไม่มี baseline 79,000 หรือ savings 18,500 ที่แสดงเป็นผลพร้อมใช้; ข้อความบอก prior usage unsupported |
| C01-AC06 | shared usage unknown vs explicit zero vs complete empty list | unknown → REQUIRES_INPUT; zero/empty known → supported path; ไม่ normalize unknown เป็น zero |
| C01-AC07 | Parent eligibility None vs False vs True | None → REQUIRES_INPUT; False ไม่หัก; True หนึ่งรายหัก 30,000 ตาม caller assertion และกฎเดิม |
| C01-AC08 | พร้อมกัน: material unsupported income, retirement และ unknown parent | precedence/status ถูกต้อง; เหตุผลคงที่; ไม่เผยตัวเลขภาษี |
| C01-AC09 | ผ่าน core → discovery → guards/candidates → HTTP/UI | non-READY ไม่ถูก downstream เปิดใหม่; errors มี machine reason; consumer ไม่สร้าง baseline zero |
| C01-AC10 | หน้าเคยมีผลแล้ว เปลี่ยนเป็น input ที่ไม่รองรับ/unknown; มี response เก่า | ผล/selection/export เก่าถูกปิดและไม่กลับมา |
| C01-AC11 | Legacy seven-field / extended profile shared usage positive | ทั้งสองปิด baseline; ไม่ข้าม parser เพื่อให้ legacy ผ่าน |
| C01-AC12 | negative/malformed inputs และ unknown pool | validation/fail-closed ตาม plan; ไม่สร้าง tax authority หรือ fallback deduction |
| C01-AC13 | evidence ใหม่และ catalog version | metadata ตรง source; primary/supplementary/page ที่ใช้ตรวจได้; hash/version ใหม่; candidate binding ไม่รับ arbitrary catalog |
| C01-AC14 | same supported inputs + same new engine/artifacts | output/hash/replay identical รวม readiness/reasons/scope |
| C01-AC15 | historical snapshot ด้วย current vs matching historical artifacts | current mismatch ถูก reject; มี reproduction matching historical engine/artifacts และไม่ overwrite version เก่า |
| C01-AC16 | invalid Host/Origin/framing และ private paths | boundary เดิมทำงาน; HTTP F09 มีรายงาน diagnosis/result/remaining issue |
| C01-AC17 | critical debt/low reserve/commitments/partial financial data บน READY tax | guardrails เดิมทำงาน; ไม่ relax เงินสำรองเพื่อผ่าน tests |
| C01-AC18 | supported family/mortgage/PIT boundaries | fixtures อิสระไม่ regress; การเปลี่ยน tests จาก scope ใหม่มี mapping และเหตุผล |

ตัวเลข C01-AC01 ใช้เพื่อรักษากรณี supported เดิม
กรณี “ยอดลงทุนเดิม 100,000 รวม baseline แล้ว ซื้อใหม่อีก 100,000 ประหยัด 15,000”
เป็น acceptance ของ C02 เมื่อมี treatment จริง; C01 ต้อง block กรณีนี้ ไม่แสร้งคำนวณครบ

## 10. Engineering และการตรวจ

- ใช้ typed immutable models และ pure domain functions เดิม; ไม่สร้าง generic rules DSL
- ผู้พัฒนาเลือก module layout, error envelope และ archived artifact layout ได้ใน plan
  ภายใต้ observable contract นี้ ต้องบันทึกตัวเลือกก่อนลงโค้ดและผูก tests
- readiness เป็น domain contract ไม่ใช่ validation ของหน้าเว็บอย่างเดียว
- ใช้ locked dependencies และ Python 3.12 CI ตาม repo; บันทึก local runtime จริงแยกกัน
- meaningful regression/golden/boundary/replay tests; existing tests ต้องยังตรวจความหมายเดิม
  ใน supported scope และ tests ที่เปลี่ยนตาม C01 ต้องชี้ acceptance ID

Quality commands ตาม repo:

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict
uv run --locked pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run --locked python -m examples.check_web_demo
uv build
```

รักษา core coverage gate ที่มีอยู่ 100% statements/branches
coverage เป็น regression evidence ไม่แทน external legal/golden verification
บันทึก remote CI exact SHA เมื่อมีการ push/PR จริง ไม่อ้างจาก run คนละ SHA

## 11. Deliverables และ definition of done

Implementation deliverables ในงาน C01:

- core/adapter contracts, source artifacts และ version changes ตาม scope
- acceptance tests และ evidence mapping C01-AC01–18
- README/examples/input contracts ที่ปรับคำว่า READY และ known zero ให้ตรง
- migration notes สำหรับ input, status, new engine/catalog และ historical replay
- `docs/implementation-reports/TGPS-C01.md` พร้อม commands/results/runtime/commit,
  evidence verification, deviations และ F09 diagnosis
- roadmap status และ Decision Log ที่อัปเดตจากหลักฐานจริง

C01 รับงานได้เมื่อ acceptance matrix ผ่าน, material legal evidence พร้อม,
regression/quality gates ผ่าน และ review record ระบุ version/commit ที่รับ
ถ้ากฎหมายหรือ F09 ยังเปิดอยู่ ให้บันทึกความไม่ครบและสถานะจริง
ไม่เลื่อน roadmap เป็น ACCEPTED จากการเขียนสเปกหรือแค่ tests ผ่าน

## 12. Decisions และเรื่องที่ผู้พัฒนาตัดสินได้

ขอบเขตและลำดับ C01 ผู้ใช้ตกลงแล้ว รายละเอียด statuses/reasons/precedence,
explicit shared unknown และ migration เป็น proposal ที่ผู้เขียนกำหนดให้สเปกตรวจได้
บันทึกใน [DEC-006–008](../DECISIONS.md)

ผู้พัฒนาเลือก physical modules, filenames ของ archives, error envelope ตาม conventions,
วิธีวินิจฉัย HTTP และจำนวน repeated runs ที่เหมาะกับ hypothesis ได้
หากพบว่าต้องเพิ่ม deduction treatment ใหม่, relax guardrails, ขยายประเภทเงินได้
หรือเปลี่ยนพฤติกรรม readiness จากสเปกนี้ ต้องบันทึก requirement revision ก่อนทำ

## 13. Requirement review record

- Date: `2026-10-15`
- Method: fresh builder check อ่าน requirement นี้พร้อม roadmap และ decision log
  เพื่อหาคำถามที่ต้องเดาจนเปลี่ยน implementation plan
- Result: `nothing important left` — ไม่พบคำถามสำคัญที่ค้างก่อนวางแผน
- Meaning: ตรวจความพร้อมของสเปกสำหรับ planning เท่านั้น ไม่ใช่ผล tests,
  การยืนยันกฎหมาย, การอนุมัติรายละเอียดแทนผู้ใช้ หรือ milestone acceptance

## Change log

| Date | Version | Change | Status |
| --- | --- | --- | --- |
| 2026-10-15 | 0.1 | เขียนรายละเอียด C01 จาก roadmap ที่ผู้ใช้ตกลง พร้อม acceptance/migration boundaries | REQUIREMENT_REVIEW; implementation NOT_STARTED |
| 2026-10-15 | 0.1 | สถานะ implementation เป็น IN_PROGRESS; Task 1 เสร็จ, Task 2–3 บางส่วน; เนื้อหา requirement ไม่เปลี่ยน | [DEC-009](../DECISIONS.md#dec-009--เริ่ม-implementation-c01-และการติดตามความคืบหน้า) |
