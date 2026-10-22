# TGPS-C02 — Progress ledger

Requirement: [v0.1 — scope/behavior approved; evidence review open](../requirements/TGPS-C02-existing-rights.md)

Status: **REQUIREMENT_REVIEW / implementation NOT_STARTED**

## 2026-10-15

- [x] ร่าง PVD/RMF/Thai ESG, readiness, authoritative usage, การไม่หักซ้ำ,
  employee/employer separation, version/replay boundaries และ C02-AC01–12
- [x] Source reconnaissance พร้อมจุดอ้างอิง/ข้อจำกัดใน requirement §6;
  ยังไม่ certify กฎหมายปี 2569 และไม่แก้ released pack/catalog
  พบ RD RMF FAQ เก่า จึง mark REJECTED สำหรับกฎปัจจุบันเพื่อไม่ใช้ซ้ำ
- [x] Fresh builder check ตาม brainstorming skill: `c02_builder_check` read-only;
  verdict “nothing important left” นอก legal/approval gates ที่ร่างระบุแล้ว
  เป็นการตรวจความชัดของร่าง ไม่ใช่ legal review หรือผู้ใช้รับงาน
- [ ] ผู้ใช้อนุมัติ requirement รายละเอียด
- [ ] Legal evidence matrix + independent numeric fixtures
- [ ] Implementation plan → RED/GREEN → full verification → review → acceptance

วิธีทำ: ใช้ requirement/ledger เดิมของ repo แทนสร้าง design ซ้ำอีก directory;
รายละเอียดที่ผู้เขียนเสนอแยกจากข้อตกลงผู้ใช้. ไม่มี product code ของ C02,
ไม่มี C02 RED/GREEN หรือ test pass ที่จะรายงาน; regression ที่ผ่านเป็น C01/UI01
ตาม [handoff verification](TGPS-handoff-verification.json)

## 2026-10-21 — เตรียมรีวิวรายละเอียด

- [x] จัด [review brief](../requirements/TGPS-C02-review-brief.md) ย่อ v0.1-draft:
  PVD ลูกจ้าง → RMF → Thai ESG, authoritative baseline/capacity, unknown/readiness,
  versioning และ evidence/fixture gates. ไม่เปลี่ยน requirement หรือยืนยันกฎหมายใหม่
- [ ] อนุมัติรายละเอียด v0.1-draft หลังอ่าน requirement/brief; ยังไม่มี treatment code,
  implementation plan หรือการเปลี่ยน milestone เป็น IN_PROGRESS

## 2026-10-21 — Evidence work หลังอนุมัติ scope

- [x] ผู้ใช้ตอบ “โอเครครับ ลุย!” หลัง review brief/ขั้นตอน approval→evidence;
  บันทึก DEC-019 และ requirement v0.1: scope/behavior approved, legal review OPEN,
  implementation NOT_STARTED. รายการ approval ที่ค้างข้างบนเป็นประวัติก่อนคำตอบนี้
- [x] Baseline บน HEAD1567e86: uv sync ผ่าน16packages; Python695 passed/10.51s;
  fresh-server frontend37/37, zero failed/skipped. ไม่มี product source edits
- [x] เก็บ12 official-source artifacts (HTML/PDF), validate format + SHA256;
  MR395/MR398/DG458 ถอดข้อความเพี้ยน จึง render/readครบ13หน้า;
  expense infographicอ่านภาพ4หน้าและ PND91หน้า3/bracketsหน้า1 เพิ่ม
- [x] [Evidence matrix](../policy-evidence/2026-10-21/README.md)12แถว ผูก AC;
  แยก text-confirmed/inference/open, signed/published/applicable dates และข้อจำกัด
- [x] เขียน9 numeric fixturesด้วยมือ แล้วตรวจ Decimalแยกจากtax_gps/pack =9/9;
  เป็น PROVISIONAL arithmetic, ไม่ใช่ legal golden acceptance หรือ RED→GREEN
- [x] LOW-WAGE fixtureจับการหักPVDผิดลำดับได้จาก taxable11500เทียบ3000;
  PITทั้งสองเป็น0 จึงห้ามตรวจแค่PIT. ข้อมูลทั้งหมดsynthetic
- [ ] G1–G6: qualifying PVD wages/multi-employer, independent order review,
  RMF exempt-income basis/future facts, paid-vs-accepted shared authority,
  2026ESGX classification/pool และ amendment/independent review ยังOPEN
- Task evidence: PARTIAL — custody/matrix/provisional arithmetic DONE;
  legal applicability/independent approval pending. ไม่มี implementation plan,
  treatment/readiness changes, released pack/catalog edits หรือ C02 acceptance
- Final full locked gates: sync/lint/format157/mypy102/build0.2.0 passed;
  Python suite and100%statement/branch gate passed; fresh-server frontend37/37,
  zero fail/skip. Windows CPython3.14.3/Node24.3.0; no new remoteCI for these docs.
  Arithmetic9/9 remains separate from product regressions/acceptance. Final audit
  checks12 source hashes, fixture receipt hash, JSON parse and absence of product diff

## 2026-10-21 — PVD evidence follow-up

- [x] ใช้ tgps-policy-evidence / tgps-mark-progress; baseline sync16packages,
  Python695 passed/11.34s และ fresh-server frontend37/37, zero fail/skip
- [x] เพิ่ม [PVD follow-up](../policy-evidence/2026-10-21/pvd-follow-up/README.md):
  Act §3 wage definition, §§5–6 fund/employee-employer distinction,
  §§9–10 contribution conditions/minister exception; MR183 §2 definitions
- [x] เก็บ MR183 HTML และ PND91 form PDF พร้อม hashes เพิ่ม2 originals รวม14;
  SEC consolidation อ่าน web textได้ แต่ direct download403 จึงบันทึก FAILED/hashnull
- [x] Render/read PND91 PDF2 ก1–7/ข1 และอ่าน PDF3 deduction8: หลักฐานแบบฟอร์ม
  ยืนยันลำดับ exemption→expense→deduction ในแบบที่ตรวจ; ไม่อ้างว่าเป็นแบบปี2569
- [x] แยก pooled-fund definition ออกจากบุคคลทำงานหลายนายจ้าง;
  ไม่พบ direct aggregation ruling ในรอบนี้ จึงยังไม่ปิด G1
- [x] ระบุข้อจำกัด scratch clipping formula สำหรับ minister-approved exceptional rates;
  9 fixturesเดิมอยู่ใน ordinary range และคง bytesเดิม ไม่เลื่อนเป็น legal golden
- Task PVD evidence: PARTIAL — definition/order corroborationเพิ่มแล้ว;
  aggregation/exception/current applicability และ G3–G6 ยังOPEN.
  Implementation NOT_STARTED; ไม่มี runtime, requirement scope หรือ released pack editsรอบนี้
- [x] Final verification: locked sync16packages; ruff clean/format158 files;
  strict mypy102 files; pytest695 passed/12.25s, statements2846/branches798
  coverage100%; fresh-server frontend37/37 (4581ms, fail0/skip0);
  build sdist/wheel0.2.0 ผ่าน บน Windows CPython3.14.3
- [x] Custody audit:14 original SHA256ตรงทั้งหมด, failed retrieval1รายการ hashnull,
  fixture receipt hashตรง และ JSONทุกไฟล์ parseผ่าน; git diff --checkผ่าน
  (มี CRLF→LF warningเดิมของ requirement). Product pathsไม่มี diff;
  เอกสาร C02 ยังไม่ commit/push และไม่มี remoteCIใหม่ของรอบนี้

## 2026-10-22 — Cross-rule evidence / review diagnostics

- [x] ผู้ใช้สั่งลุยตามรายการ PVD→RMF→ThaiESG; ใช้ tgps-policy-evidence และ
  tgps-mark-progress. Baseline locked sync16packages, pytest695/10.92s และ
  fresh-server frontend37/37, fail0/skip0 (4615ms)
- [x] เพิ่ม [joint review](../policy-evidence/2026-10-21/joint-follow-up/README.md),
  MR266/MR357 lineage: ดูภาพครบ9หน้า; แยก first-paragraph amendment ออกจาก
  shared-cap paragraphที่ยังอยู่. ไม่ใช้ MR266 percentageเก่าเป็นกฎปัจจุบัน
- [x] เก็บต้นฉบับเพิ่ม5รายการรวม19; MR401Aเป็นเรื่องท่องเที่ยว ดูหน้า1แล้ว exclude
  ไม่สับสนกับ DG401. SEC ESGX QAอ่านเว็บได้แต่ raw403/hashnull รวมfailed2รายการ
- [x] SEC QAหน้า2ข้อ4 และ MR398/DG458ที่ตรวจภาพเทียบ ยืนยันความสอดคล้องของ
  2026 common-pool interpretation; ยังไม่ certify product/class หรือเพิ่มtreatment
- [x] พบ historic RMF FAQ tax2017ข้อ2 ใช้ก่อน elderly exemption; rejectเป็น
  current-rate/PVD authority แต่บันทึกเพื่อไม่ใช้ blanket exemption inference
- Task cross-rule review: PARTIAL — lineage/pool corroborationเพิ่มแล้ว;
  RMF percentage-base interpretation, PVD aggregation/exception, fact/time/shared
  authority และ independent/currency reviewยังOPEN. ไม่มี requirement scope change,
  implementation plan, runtime edits, C02 RED/GREEN หรือ acceptance
- [x] Diagnostic arithmetic4/4: RMF basisสองสมมติฐาน PIT19785เทียบ22485
  (ต่าง2700) ไม่เลือกเป็นคำตอบกฎหมาย; conditional ESG pool PIT63500เทียบ
  wrong-extra-pool56000 (ต่าง7500). Receiptผูก fixture hash;
  9 fixturesเดิมคง bytes/receiptเดิม ไม่เลื่อนเป็น golden cases
- [x] Custody audit19 original hashesตรง, failed2รายการ hashnull;
  JSONทั้งหมด parseผ่าน และ git diff --checkผ่านพร้อม CRLF warningเดิม.
  README/ROADMAPเพิ่ม follow-upเพื่อไม่ให้ count12เก่าถูกอ่านเป็นยอดล่าสุด
- [x] Final full verification: locked sync16packages, ruff clean/format159files,
  strict mypy102files, pytest suite695/coverage100% (2846statements/798branches),
  fresh-server frontend37/37, fail0/skip0 (4613ms), build0.2.0ผ่าน;
  Windows CPython3.14.3. งานรอบนี้เป็นเอกสาร/หลักฐาน; ไม่มี product diff,
  commit/push หรือ remoteCIใหม่ และไม่ได้ปิด legal/acceptance gates
- Verification note: outputของ full-gate batchถูกตัดกลางรายงาน และอ่าน pytest
  lastfailed cacheใน sandboxถูกปฏิเสธ จึงไม่ใช้ cacheเป็นหลักฐาน;
  รัน pytest+coverageซ้ำโดย capture exit codeโดยตรง: exit0,
  695passed/11.91s, 2846statements/798branches/100%. ไม่มี test failureที่พบ

## 2026-10-22 — UX ที่เข้าใจง่ายตามคำขอผู้ใช้

- [x] อ่าน session-start/policy-evidence/brainstorming/record-decision/mark-progress;
  baseline sync16packages, pytest695/10.61s และ fresh-server frontend37/37,
  fail0/skip0 (5263ms); git status/logตรวจแล้ว คง unrelated Stage4 draft
- [x] ตรวจ requirement C02, UI02 plan และหน้า HTMLจริง: มี3กลุ่ม input,
  auto450ms, pending shell, profile/audit details และ comparisonเปิดเป็นหลัก
- [x] ร่าง [C02 UX](../requirements/TGPS-C02-guided-rights-ux.md): เปรียบเทียบ3รูปแบบ,
  เลือกเสนอหน้าเดียวแบ่งหมวด, มี/ไม่มี/ยังไม่ทราบไม่ตั้ง0, wireframes,
  ผล3ระดับ, missing/unsupported/pending/ready/error และ C02-UX01–09
- [x] DEC-020บันทึกเป้าหมายผู้ใช้แยกจาก layoutที่ผู้เขียนเสนอ;
  README/ROADMAPและ requirement change logเชื่อม draft. ไม่มี product edits
- [x] Legal search follow-upแบบจำกัด: RD queriesเรื่องนายจ้างหลายราย/สองแห่งและ
  RMFฐานเงินสะสมไม่พบข้อวินิจฉัยตรงประเด็นเพิ่มเติม; ผลที่พบเป็น pooled-fund,
  old/general codeหรือ instructionsเรื่องtransfer ไม่ใช้แทน aggregation/basis proof.
  ไม่เพิ่ม artifactซ้ำหรือเลื่อนสถานะ G1/G3 จากผลค้นหาทั่วไป
- Task UX: DRAFT WRITTEN / builder check requested; ยังไม่ใช่ user approval,
  usability test, implementation plan, RED/GREEN หรือ legal/UX acceptance
- [x] Fresh builder checkตามbrainstorming: `c02_ux_builder_check` read-onlyพบ1ข้อ
  เรื่องไม่มีซื้อใหม่แต่มีขาย/โอน/สิทธิปีก่อน; แก้ draftข้อ4/UX02ให้แยกทางข้อมูล
  และเพิ่มกรณีตรวจ. ตรวจซ้ำ verdict “nothing important left” ในขอบเขตUX draft
- [x] Full gatesตาม tgps-verify: sync16packages, ruff clean/format160,
  mypy102, pytest695/12.01s, coverage2846statements/798branches/100%,
  fresh-server frontend37/37 fail0/skip0 (4547ms), build0.2.0 exit0;
  WindowsCPython3.14.3. ดู [verification receipt](TGPS-C02-ux-draft-verification.json)
- Verification interruption: scratch report printerเจอ cp874 UnicodeEncodeError
  หลัง frontend exit0 และก่อน build; แก้ stdout encodingแล้ว resumeเฉพาะbuild.
  Receiptระบุ6 gatesแรกว่า recoverจาก exit0ที่เห็นจริง; ไม่อ้างว่ารันทุกขั้นซ้ำ.
  git diff --checkครั้งแรกพบ blank EOFใน ROADMAP แก้แล้วตรวจซ้ำผ่าน
  (คง CRLFwarningเดิม). Product pathsไม่มีdiff; ยังไม่commit/push/remoteCI
- Task UX: DRAFT REVIEWED / user layout approval pending. แบบใช้ HTML/CSS/JSเดิม,
  ยังไม่มี product implementation หรือ usability test. คำถามลำดับความสำคัญที่ส่ง
  ผู้ใช้แบบoptionalยังไม่มีคำตอบในรอบนี้; เป้าหมาย“ภาพรวมก่อน”ระบุเป็นauthor proposal
  ไม่อ้างเป็นสิ่งที่ผู้ใช้อนุมัติ. Legal G1/G3และgatesอื่นยังไม่ปิด

## 2026-10-22 — UX approved / clickable design prototype

- [x] ผู้ใช้ตอบ“โอเครครับ ลุย!”หลังรับแบบUXและสรุปflow; DEC-021บันทึก
  UXdesignapproved แยกจาก legal/runtime/acceptance. ไม่ถามlayoutเดิมซ้ำ
- [x] Baseline locked sync16packages; pytest695/10.73s;
  fresh-server frontend37/37 fail0/skip0 (4595ms)
- [x] ทำ [standalone prototype](../demo/c02-guided-rights-preview.html) ในdocs:
  missing/unsupported/ready3presets, conditionalPVD fields, separatehistory,
  error-linkfocus, editinginvalidatesreadydetails, methoddisclosuresและreset.
  ไม่มี tax formula, requestไปengine, storageหรือruntime routeใหม่
- [x] เพิ่ม field/copy inventoryในUXspec§9: ตรวจ salary→section_40_1และ
  RetirementContribution.amount_used/shared_usageจริง; ไม่reuseเป็นpaidหรือ
  authoritativeclaimโดยเปลี่ยนความหมาย. Fieldsสุดท้ายยังผูกlegal/domain review
- [x] ใช้ connected Chromeตรวจ initialchoices, ready→editซ่อนdetails,
  error-linkfocus=pvd-wage, ไม่มีซื้อใหม่แต่historyยังvisible, methoddisclosure;
  viewport390และ320ไม่ล้นแนวนอน คืนviewport/initialpresetแล้วเปิดแท็บให้ลอง
- [x] เก็บ [desktop](../demo/c02-guided-rights-preview-desktop.jpg) /
  [mobile](../demo/c02-guided-rights-preview-mobile.jpg). Browsererrorlogsว่าง;
  ยังไม่อ้าง fullkeyboard/usability/financialvalidation หรือ legalacceptance
- Task UX prototype: BUILT / browser spot-check DONE; parent C02 treatment
  NOT_STARTED. Implementation planยังไม่สร้างตามlegal gate; ไม่เปลี่ยน
  engine, API, readiness, versioned assetsหรือ milestone acceptance
- [x] [Prototype review receipt](TGPS-C02-ux-preview-review.json): servedbytesตรง
  HTMLบนดิสก์, nonallowlisted `/AGENTS.md`ได้404; hash3artifactsและbrowser
  observationsบันทึกแล้ว. Previewเฉพาะ127.0.0.1บนportสุ่ม; ไม่ใช้server8765เดิม
- [x] [Full verification](TGPS-C02-ux-preview-verification.json): ทุกgateexit0,
  sync16packages/ruffclean/format160/mypy102, pytest695/12.51s,
  2846statements/798branches/100%, fresh-serverfrontend37/37 fail0/skip0
  (4679ms), build0.2.0ผ่าน WindowsCPython3.14.3. git diff --checkผ่าน;
  productpathsไม่มีdiff. เอกสาร/prototypeยังไม่commit/push/remoteCI

## 2026-10-22 — Targeted legal follow-up / C02A scope proposal

- [x] Session-start/policy-evidence/mark-progress/record-decisionใช้ตามrepo;
  baseline sync16packages, pytest695/10.87s, fresh-serverfrontend37/37,
  fail0/skip0 (4819ms). ตรวจgitstatus/logและคงunrelatedStage4draft
- [x] ค้นRD-focusedแบบจำกัดเฉพาะmultiple/twoemployers, >15%และRMFwithPVD;
  ยังไม่มีdirectindividualrulingเพิ่มเติมที่ใช้ปิดG1/G3. Corporate0706/4613,
  oldinstructions/FAQและsnippetทั่วไปไม่ใช้แทนข้อสรุปนั้น
- [x] เก็บ [SETarticle+2tables](../policy-evidence/2026-10-22/README.md),
  HTML/PNGmagicและhash; อ่านตารางต้นฉบับทั้ง2ภาพ. ตัวอย่างsalary600000 /
  PVD90000 / RMF180000 และsalary1000000 / PVD150000 / RMF300000
  corroborateก่อนPVDexemption แต่เป็นeducational2021ไม่ใช่RDlegalclosure2026
- [x] เพิ่ม3originalsรวม22 (ไม่ใช่22approvedrules), ไม่เปลี่ยน19originalsเดิม;
  webimagecachemissแก้โดยGETexactlinkedURLs สำเร็จ ไม่เดาURLหรือใช้snippetแทนภาพ
- [x] ร่าง [C02A](../requirements/TGPS-C02A-pvd-first-slice.md) เป็นข้อเสนอแยก:
  normalpositivePVDนายจ้าง/กองทุนเดียวก่อน, otherpositives/unknownปิดผล,
  positivePVDbaselineแสดงได้เมื่อผ่านreviewแต่newcashยังไม่เปิด;
  zeroPVDคงsupportedเดิมเมื่อfactsครบ. ไม่เปลี่ยนapprovedscopeเงียบๆ
- [x] Freshbuildercheck`c02a_scope_check`ตามbrainstormingพบ3คำถาม:
  positive/zero coverage, grosssalaryก่อนPVDและconsumeravailability.
  แก้ให้ชัด+ตรวจcatalogจริงไม่มีRMFnewcashdefinition; reviewซ้ำ“nothing important left”.
  เป็นscopeclarityreview ไม่ใช่legalcertificationหรือuserapproval
- [x] C02Aconditionalarithmetic9/9 ผูกfixturehash, split9999/10000/10001,
  cap499999/500000/500001/paid600000และlowwage; ไม่มีRED/GREENหรือengineimports
- [x] DEC-022เป็นAUTHORING_DETAIL / REQUIREMENT_REVIEWเท่านั้น;
  README/ROADMAP/parentchangelogเชื่อมproposalโดยไม่เปลี่ยนC02status
- Task legal closure: PARTIAL — grossbasecorroborationเพิ่ม; G1/G3directapplicability
  ยังOPEN. Task C02A: PROPOSED / userstagedscopeapproval pending; ไม่มีplan/code
- [x] Custodyaudit:22originalhashesตรง, failed2hashnull, 3ชุดarithmeticreceipts
  fixturehashตรงและJSONทุกไฟล์parseผ่าน. Sourcecountรวมsupplementary/excluded
  ไม่ใช้จำนวนไฟล์เป็นหลักฐานปิดgate
- [x] [Final verification](TGPS-C02A-scope-review-verification.json): ทุกgateexit0;
  sync16/ruffclean/format162/mypy102, pytest695/12.90s,
  coverage2846statements/798branches/100%, fresh-serverfrontend37/37
  fail0/skip0 (5732ms), build0.2.0ผ่าน WindowsCPython3.14.3.
  git diff --checkผ่านพร้อมCRLFwarningเดิม; productpathsไม่มีdiff,
  ไม่มีcommit/push/remoteCIหรือการอนุมัติscopeแทนผู้ใช้

## 2026-10-22 — C02A approved scope / scoped evidence review

- [x] ผู้ใช้อนุมัติ staged scope ของ C02A หลังข้อเสนอ; เพิ่ม DEC-023 และปรับ requirement/roadmap โดยคง DEC-022 เป็นประวัติข้อเสนอ
- [x] Session baseline: sync16, pytest695/11.04s; fresh-server frontend37/37 fail0/skip0 (4809.5112ms). ยังไม่มี product edits
- [x] Independent read-only evidence review `c02a_evidence_review`: คำนวณ Decimal แยก 9/9 ตรง; พบ important gaps สองจุดคือ bounded current-applicability review และ qualifying-fund chain ของ allowance. ไม่เรียก arithmetic pass ว่า legal pass
- Task C02A scope: AGREED_DIRECTION; evidence PARTIAL / implementation NOT_STARTED. ตรวจสองประเด็นต่อก่อนเขียนแผน ไม่ขออนุมัติ scope ซ้ำ
- [x] Scoped gapsปิดสำหรับplanningตามDEC-024; newnormalreference9/9, custody26originals/failed4และfourreceiptsผ่านhashaudit. Parentlegalgatesไม่ถูกปิดรวม
- [x] [C02A ledger](TGPS-C02A-progress.md) และ [แผน4tasks](../superpowers/plans/2026-10-22-c02a-normal-pvd.md)พร้อมself-review; DRAFT_FOR_REVIEW / implementation NOT_STARTED. Nativeเป็นข้อเสนอ ยังไม่เลือกแทนผู้ใช้
- [x] Finalgatesทั้งหมดexit0ตาม [receipt](TGPS-C02A-plan-verification.json): pytest695/11.36s, statements2846/branches798/100%, frontend37/37 fail0/skip0/4483.5213ms, ruffformat165/mypy102/build0.2.0. No product edits/commit/push/acceptance
