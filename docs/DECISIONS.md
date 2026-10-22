# Tax GPS — Decision Log

บันทึกข้อตกลงและเหตุผลเพื่อใช้ย้อนรีวิวร่วมกับ [Roadmap](ROADMAP.md)
วันที่ใช้ Asia/Bangkok รายการใหม่เพิ่มท้ายไฟล์; หากเปลี่ยนข้อตกลง ให้เพิ่ม decision ใหม่
และอ้างรายการที่เปลี่ยน ไม่ลบเหตุผลเดิม

คำว่า AGREED ใช้เฉพาะสิ่งที่ผู้ใช้ตกลงแล้ว
AUTHORING_DETAIL หมายถึงรายละเอียดที่ผู้เขียนเสนอเพื่อทำสเปกให้รีวิวและนำไปวางแผนได้
ไม่อ้างว่าผู้ใช้ได้อนุมัติทุก enum/API/วิธี migration ที่ยังไม่ได้อ่าน

## DEC-001 — Roadmap และผู้ใช้กลุ่มแรก

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: ใช้ roadmap หกช่วง: correctness → existing rights → annual estimate →
  allocation experiments → time-based comparison → continued use
- Initial user scope: พนักงานเงินเดือน 40(1), ปีภาษี 2026 / พ.ศ. 2569
- Reason: ต่อจาก salary core ที่มีอยู่ และทำฐานภาษีให้ถูกก่อนใช้เปรียบเทียบเงินก้อนใหม่
- Evidence: ผู้ใช้ตอบ “โอเคร เยี่ยมเลยครับ ลุย!” หลังข้อเสนอ roadmap และ requirement แรก
- Documents: [ROADMAP](ROADMAP.md), [Product Review](reviews/2026-10-15-product-domain-review.md)

## DEC-002 — งานแรกเป็น baseline integrity

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: เริ่ม TGPS-C01 ปิดปัญหา retirement, shared usage, unknown eligibility,
  source provenance และตรวจ HTTP failure ที่พบก่อนเพิ่ม deduction categories
- Reason: ผลประหยัดภาษีของเงินใหม่ต้องเริ่มจาก baseline ที่ไม่ตกหล่น
- Deliverable: [TGPS-C01 requirement](requirements/TGPS-C01-baseline-integrity.md)
- Boundary: การรองรับ RMF/PVD/ประกันเป็น deduction จริงอย่างครบเงื่อนไขอยู่ช่วง C02

## DEC-003 — จัดเก็บ requirement, roadmap และประวัติเป็น Markdown

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: เก็บ roadmap ใน `docs/ROADMAP.md`, requirement รายช่วงใน
  `docs/requirements/`, และข้อตกลงในไฟล์นี้
- Reason: ต้องเห็น log, ทวนขอบเขต และรีวิวได้ใน repo
- Lifecycle: AGREED_DIRECTION/REQUIREMENT_REVIEW แยกจาก implementation และ acceptance
- Scope of this record: บันทึกทิศทางและจัดทำ requirement; ยังไม่มีหลักฐาน implementation C01

## DEC-004 — จุดส่งมอบ MVP

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: จบ C03 เป็น MVP สำหรับดูภาษี; จบ C05 เป็น MVP สำหรับเปรียบเทียบการใช้เงิน
- Reason: เป็นผลลัพธ์ที่ผู้ใช้ใช้ได้ โดยไม่ผูกทุกความสามารถเข้ากับการเปิดตัวครั้งเดียว
- Qualification: แต่ละ MVP ใช้ได้เฉพาะ declared coverage ที่ผ่านการตรวจแล้ว

## DEC-005 — ลำดับ persistence และการกำหนดเวลา

- Date: `2026-10-15`
- Status: `AGREED` สำหรับลำดับหลัก; `AUTHORING_DETAIL` สำหรับวิธีติดตามเวลา
- Decision: งานใช้งานต่อเนื่องอยู่ C06; draft storage ขนาดเล็กแทรกได้เมื่อจำเป็น
  โดยมี requirement แยกและบันทึกการเปลี่ยนลำดับ
- Existing draft: [Stage 4](demo/stage4-local-profile-contract-draft.md) ยังเป็น draft
- Authoring detail: ไม่ตั้งเส้นตายสมมุติ; ประเมินขนาดงานหลังรีวิว requirement รายช่วง
- Reason: ความถูกต้องของภาษีและประโยชน์ในการทดลองมาก่อนการขยาย storage

## DEC-006 — พฤติกรรมที่เสนอเพื่อปิด C01

- Date: `2026-10-15`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW`
- Proposal: material retirement และ positive shared usage ที่ยังไม่มี baseline treatment
  คืน UNSUPPORTED; unknown ที่มีผลต่อ baseline คืน REQUIRES_INPUT; ไม่เผย PIT หรือ candidates
- Proposal: explicit zero shared usage ยังใช้ supported salary path ได้; null ไม่ใช่ zero
- Proposal: READY หมายถึงพร้อมภายใน declared supported coverage เท่านั้น
- Reason: ไม่สร้าง tax eligibility/deduction treatment ใหม่ในงานแก้ความถูกต้อง
- Consequence: บาง input ที่เคยคืน READY หรือเฉพาะ capacity จะเปลี่ยนผล ต้องมี migration,
  engine version และ regression cases ที่ชี้ว่าพฤติกรรมเปลี่ยนโดยตั้งใจ
- Details: C01 sections 4–8 และ acceptance matrix

## DEC-007 — การรักษาผลเก่าและหลักฐานกฎหมาย

- Date: `2026-10-15`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW`
- Proposal: ตรวจ source ตรง rule และออก artifact version ใหม่; เก็บ artifact เก่า
  สำหรับ replay ที่ระบุ version/hash ชัดเจน โดยไม่ถือว่าเก่าเป็น current production authority
- Reason: การมี hash และ official URL เพียงอย่างเดียวไม่พิสูจน์กฎหมาย และการแก้ bundle
  ใต้ version เดิมทำให้ผลย้อนหลังตรวจไม่ได้
- Current acceptance: ไม่มี decision นี้ที่รับรอง P1-004 หรือ waive gate เดิม

## DEC-008 — รูปแบบเอกสารเทียบกับการอนุมัติรายละเอียด

- Date: `2026-10-15`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW`
- Decision: ขอบเขต C01 และ roadmap ตกลงแล้ว; สเปกรายละเอียดที่จัดทำให้มีสถานะ
  REQUIREMENT_REVIEW และ implementation NOT_STARTED จนมีการรีวิว/เริ่มงานจริง
- Reason: ให้ log แยกสิ่งที่ผู้ใช้ตกลงในบทสนทนาจากรายละเอียดทางเทคนิคที่เพิ่งเขียน
- Next record: เมื่อยืนยันรายละเอียดหรือเริ่ม implementation ให้เพิ่ม entry และอ้าง version
  ที่ใช้ ไม่แก้ entry นี้ย้อนหลังให้ดูเหมือนโค้ดได้พัฒนาแล้ว

## DEC-009 — เริ่ม implementation C01 และการติดตามความคืบหน้า

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: เริ่ม implementation TGPS-C01 v0.1 ตาม
  [plan](superpowers/plans/2026-10-15-c01-baseline-integrity.md); สถานะเป็น IN_PROGRESS
- Evidence: plan บันทึกว่าผู้ใช้อนุมัติด้วย “โอเครครับ ลุย!”; ผู้ใช้สั่งให้แก้ test ที่พัง
  และทำ Task 2 ต่อในบทสนทนา 2026-10-15
- Tracking: ผู้ใช้ขอให้ทำเครื่องหมายในเอกสารทุกครั้งที่ทำงานเสร็จ ว่าทำอะไรไปแล้วและทำอย่างไร
  ใช้ checkbox + บรรทัด `↳ ทำแล้ว:` ใน plan, สถานะ task ใน ledger และสถานะใน requirement/roadmap
- Boundary: แก้เฉพาะสถานะ ไม่เปลี่ยนเนื้อหา DEC-006/007 หรือ acceptance ของ C01;
  IN_PROGRESS ไม่ใช่ IMPLEMENTED หรือ ACCEPTED

## DEC-010 — กติกากลางสำหรับ AI agent และ skill set มาตรฐาน

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: เพิ่ม `AGENTS.md` ที่ root เป็นแหล่งกติกาเดียวที่ agent/model ทุกตัวต้องอ่านก่อนทำงาน
  พร้อม skill set มาตรฐาน 7 ตัวใน `.claude/skills/` (session-start, implement-task, verify,
  mark-progress, record-decision, policy-evidence, git); `CLAUDE.md` และ
  `.github/copilot-instructions.md` ชี้มาที่ `AGENTS.md`
- Evidence: ผู้ใช้ขอ “ช่วยเขียน agent skill ติดไว้กับ repo … ทุกครั้ง ทุก model ก่อนที่จะทำอะไร
  ต้องมาอ่าน agent.md ไฟล์นี้ก่อนเสมอ เพื่อไม่ให้หลุดกรอบที่วางไว้”
- Reason: ให้ agent ต่างตัวทำงานด้วยมาตรฐาน คำสั่ง และขอบเขตเดียวกัน
- Boundary: ไม่เปลี่ยน requirement, สถานะ milestone หรือสัญญาโค้ด; กติกาใน `AGENTS.md`
  สรุปจาก ROADMAP/DECISIONS/requirements ที่มีอยู่ ถ้าขัดกัน เอกสารต้นทางและ DEC ใหม่มีผลก่อน


## DEC-011 — C01 IMPLEMENTED และจุดรับช่วงที่ไม่ทำงานเดิมซ้ำ

- Date: `2026-10-15`
- Status: `AGREED` สำหรับทำ C01 ส่วนที่เหลือต่อและ mark ความคืบหน้า; `IMPLEMENTATION_EVIDENCE` สำหรับผลตรวจในเครื่อง
- Decision: บันทึก C01 เป็น IMPLEMENTED ตาม requirement v0.1/plan Task 1–5 พร้อม fresh-review fix-pass; ยังไม่ ACCEPTED และ F09 OPEN / acceptance conditional
- Evidence: ผู้ใช้สั่ง “ช่วยทำที่เหลือหน่อย ส่วนตรงไหนที่ทำเสร็จแล้วก็ mark ไว้ด้วยว่าทำไว้แล้ว ... ถ้าทำโดยใช้วิธีอื่นก็เขียนหมายเหตุไว้ด้วย”; ผลจริง 694 Python tests, coverage 100% statements/branches, frontend 24/24, lint/format/strict mypy/build ผ่าน; reviewer พบ 2 Important แล้วแก้ด้วย RED→GREEN
- Method: inline Windows + tracked ledger แทน POSIX bookkeeping; Git archive ของ pre-C01 เป็น engine เก่าสำหรับ replay แทนสลับไฟล์เดิมหรือสร้าง compatibility engine; characterization ของงานที่มีอยู่แล้วแยกจาก RED→GREEN
- Reason: ให้ session ถัดไปรับช่วงจากหลักฐานและข้อค้างจริง ไม่ทำ Task 1–5 ซ้ำเพราะเอกสารเก่า/checklist ไม่อัปเดต
- Boundary: F09 ยังไม่ยืนยันสาเหตุเดิม; ไม่ waive independent acceptance ของ C01/P1-004, ไม่รับรองกฎหมายทั้งหมดหรือ remote CI/Python 3.12/manual visual, ไม่อนุญาต push/merge และไม่เริ่ม C02 หรือเพิ่ม deduction treatment
- Records: [implementation report](implementation-reports/TGPS-C01.md), [review disposition](implementation-reports/TGPS-C01-review.md), [progress ledger](implementation-reports/TGPS-C01-progress.md)

## DEC-012 — ทิศทางปรับหน้าตาตาม fintech template

- Date: `2026-10-15`
- Status: `AGREED_DIRECTION` สำหรับใช้ reference; `AUTHORING_DETAIL / REQUIREMENT_REVIEW` สำหรับรายละเอียด layout ที่เสนอ
- Direction: ผู้ใช้ขอปรับหน้าตา Tax GPS ให้ประมาณ [Fintech SaaS template ของ Kedhareswer](https://21st.dev/@kedhareswer/templates/fintech-saas-landing-page-template)
- Evidence: “อยากให้ template ประมาณนี้ ลองเปลี่ยนให้หน่อย ได้ไหม ?” พร้อม URL
- Proposal: งานนำเสนอแยก TGPS-UI01 ใช้ cream/forest frame, centered Thai hero, circuit accents และ dashboard panels ของเครื่องคำนวณจริง; ปุ่มเชื่อม input/scenario ที่มีอยู่
- Boundary: ยังไม่ถือว่าผู้ใช้อนุมัติรายละเอียดทุกข้อ; ตาม AGENTS.md §5 จัด requirement ให้รีวิวก่อน product-code edits. ไม่เปลี่ยน C01/C02 tax contracts, readiness, guardrails, privacy, policy versions หรือ acceptance; C02–C06 ยังคงลำดับเดิม
- Records: [UI01 requirement](requirements/TGPS-UI01-fintech-restyle.md), [UI01 progress](implementation-reports/TGPS-UI01-progress.md)

## DEC-013 — เริ่ม UI01 ตามแบบที่ผู้ใช้อนุมัติ

- Date: `2026-10-15`
- Status: `AGREED`
- Decision: ทำ UI01 v0.1 ต่อแบบ inline ตาม plan โดยไม่ถามอนุมัติแบบเดิมซ้ำ
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังรับลิงก์ requirement และคำอธิบาย cream/forest frame, centered Thai hero, local CTAs และ dashboard panels
- Method: คง checkout/งาน C01 เดิม; native HTML fragment links + CSS/SVG ในเครื่อง ไม่ย้าย framework หรือเพิ่ม runtime dependencies
- Boundary: ไม่เปลี่ยนภาษี/readiness/guardrails/policy/acceptance ของ C01–C06; visual QA ที่ยังทำไม่ได้ต้องแสดง UNVERIFIED ไม่อ้างว่าผู้ใช้รับงานแล้ว
- Records: [UI01 plan](superpowers/plans/2026-10-15-ui01-fintech-restyle.md), [UI01 progress](implementation-reports/TGPS-UI01-progress.md)


## DEC-014 — UI01 implemented พร้อมแยก visual acceptance

- Date: `2026-10-15`
- Status: `IMPLEMENTATION_EVIDENCE`
- Decision: UI01 v0.1 เป็น IMPLEMENTED จาก source review/automatic gates และ preview จริง; ยังไม่ ACCEPTED เพราะ rendered visual gates ไม่มีหลักฐาน
- Evidence: Python695/coverage100%, frontend24, lint/format/mypy/buildผ่าน; source reviewerไม่มี Critical/Important/Minor ที่ยืนยันได้; preview64946 smoke9/9
- Method: HTML fragment links แทน navigation JS, local CSS/SVG แทน framework/template import; original IDs/JS/assetsตรวจคงเดิม; no browser provider จึงไม่อ้าง screenshot/keyboard visual QA
- Boundary: C01/C02–C06 tax contracts/acceptance/readiness/guardrails/pack/catalogไม่เปลี่ยน; F09ยังOPEN; remote CI/Python3.12ไม่ยืนยัน; ไม่มี commit/push/merge
- Next review: ภาพ1440/390/360, Thai clipping/overflow, real focus/scroll และความใกล้เคียง reference โดยผู้ใช้/เครื่องมือที่เข้าถึง browserได้
- Records: [UI01 report](implementation-reports/TGPS-UI01.md), [source review](implementation-reports/TGPS-UI01-review.md), [progress](implementation-reports/TGPS-UI01-progress.md)

## DEC-015 — เก็บ checkpoint และร่าง C02 เพื่อรีวิว

- Date: `2026-10-15`
- Status: `AGREED` สำหรับงานรับช่วง/commit/ตรวจ Python3.12/ร่าง C02 ตามที่เสนอ; `AUTHORING_DETAIL / REQUIREMENT_REVIEW` สำหรับรายละเอียด C02
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังเสนอ visual review, review C01/F09, commit/CI และร่าง C02; ย้ำ “if not please continoue” หลังการขัดจังหวะ
- Decision: เก็บ C01/UI01 ที่ตรวจแล้วเป็น local checkpoint; C02 เปลี่ยนจาก PLANNED เป็น REQUIREMENT_REVIEW โดย implementation NOT_STARTED
- Method: isolated Windows CPython3.12.14 แทนกล่าวอ้าง remote CI; 695 tests/100% coverage/frontend24 และทุก gate ผ่านทั้ง3.12/3.14. เก็บ raw outputs แยก; Node24.3.0 local ไม่ใช่ Node22/Ubuntu ของ CI. CUA ไม่มี provider จึง rendered review ยัง UNVERIFIED
- Authoring detail: C02 เสนอ PVD → RMF → Thai ESG; แยกยอดจ่าย/เข้าเกณฑ์/ใช้จริง, ตรวจ exemption ordering และ authoritative shared usage, ไม่เลือก tax election แทนผู้ใช้; legal matrix และ numeric fixtures ยังเป็น gate
- Boundary: ไม่มี treatment/readiness/rule changes ของ C02, ไม่ปิด F09 หรือ acceptance; ไม่ push/PR/merge ก่อนยืนยันตาม AGENTS §7 / tgps-git
- Records: [C02 requirement](requirements/TGPS-C02-existing-rights.md), [C02 ledger](implementation-reports/TGPS-C02-progress.md), [local verification](implementation-reports/TGPS-handoff-verification.json)

## DEC-016 — อนุญาต push และ draft PR เพื่อตรวจ remote CI

- Date: `2026-10-15`
- Status: `AGREED`
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังถามชัดเจนเรื่อง push branch และเปิด draft PR เพื่อรัน CI
- Decision: push feature/tgps-c01-baseline-integrity และเปิด draft PR เข้า main; ตรวจและบันทึก CI ตาม SHA จริง
- Result: ส่ง c4527c9e2a2c3b041ff72e96ac5f404c06a94170 และเปิด [draft PR #4](https://github.com/nawariso/Tax-GPS/pull/4); GitHub ตรวจว่า mergeable แต่ยังไม่ได้ merge
- Boundary: อนุญาตการ push ของงานนี้และอัปเดตหลักฐานต่อเนื่อง ไม่ได้อนุญาต merge, เปลี่ยนเป็น ready-for-review, รับงาน C01/UI01 หรือเริ่ม treatment C02; F09/visual acceptance ยังคงเดิม

## DEC-017 — UI02 guided form และ automatic calculation

- Date: `2026-10-20`
- Status: `AGREED` / `IMPLEMENTATION_EVIDENCE`; not ACCEPTED
- Evidence: ผู้ใช้เลือกทำด้วย Codex, ยืนยันโปรเจกต์ tax-gps และอนุมัติแบบ UI02 ด้วย “โอเครครับ ลุย!” หลังอ่านข้อเสนอ
- Decision: ขยาย presentation JS จาก UI01 เป็น UI02 แยก: guided inputs, auto450ms, stable pending shell, destination-value motion, error navigation และแจ้ง selection reset. ไม่แสดง stale output และยังใช้ domain readiness เดิม
- Result: Python695/coverage100%/frontend37, full locked gates/source review/fix pass และ Chrome1440/390/360 ผ่านตามหลักฐาน; reduced-motion runtime/user acceptance pending
- Boundary: ไม่เปลี่ยน C01 F09/C02–C06, legal treatment, policies/catalogs, guardrails, privacy/storage; no commit/push/merge
- Records: [requirement](requirements/TGPS-UI02-guided-live-calculation.md), [plan](superpowers/plans/2026-10-20-ui02-guided-live-calculation.md), [report](implementation-reports/TGPS-UI02.md)

## DEC-018 — เก็บ UI checkpoint และตรวจ CI ของชุดใหม่

- Date: `2026-10-21`
- Status: `AGREED` สำหรับ checkpoint/CI และเตรียมรีวิว C01/C02
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังเสนอเก็บ checkpoint งานปัจจุบัน แล้วรีวิว C01 และเตรียม C02
- Decision: commit งาน UI01 follow-up/UI02 และเอกสารที่ตรวจแล้วบน feature branch เดิม; push เข้า draft PR เดิมเพื่อตรวจ CI ของ SHA ใหม่ แยก code/documentation commits และเว้น unrelated Stage4 draft
- Reason: เก็บงานที่ผ่าน local verification/reduced-motion runtime แล้ว ก่อนเดินต่อ requirement/evidence gates
- Boundary: supersedes ข้อ no commit/push ของ DEC-017 เฉพาะ checkpoint นี้; ไม่ merge, ไม่เปลี่ยน draft status, ไม่ถือว่าผู้ใช้รับงาน UI/C01 และไม่อนุมัติ C02 treatment/readiness หรือปิด F09

## DEC-019 — อนุมัติขอบเขต C02 และเริ่ม evidence/fixtures

- Date: `2026-10-21`
- Status: `AGREED` สำหรับ scope/behavior และการตรวจหลักฐาน; กฎตัวเลข/coverage รายละเอียดอยู่ evidence review
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังได้รับลิงก์ C02 review brief และแจ้งว่าขั้นต่อไปคืออนุมัติรายละเอียดแล้วตรวจหลักฐานกฎหมาย/ตัวอย่างคำนวณก่อนลงโค้ด
- Decision: ใช้ requirement C02 v0.1 ตาม brief: PVD เงินสะสมลูกจ้าง → RMF → Thai ESG; baseline/capacity authority เดียว, ไม่หักซ้ำ, unknown/readiness/version boundaries เดิม; เริ่มเก็บ primary sources และ independent arithmetic fixtures
- Reason: ต้องพิสูจน์ deduction treatment/เพดาน/เงื่อนไขก่อนเขียน implementation plan
- Boundary: C02 ยัง REQUIREMENT_REVIEW / implementation NOT_STARTED จน evidence gate ผ่าน; ไม่ certify กฎหมายจากการอนุมัติของผู้ใช้, ไม่ข้าม C01 acceptance/F09, ไม่แก้ released assets, ไม่ merge และไม่อนุมัติ scope ใหม่ที่ไม่อยู่ v0.1

## DEC-020 — ออกแบบ C02 ให้ข้อมูลมากแต่เข้าใจง่าย

- Date: `2026-10-22`
- Status: `AGREED` สำหรับเป้าหมายความเข้าใจง่ายและการจัดทำแบบ; layout/interaction รายละเอียดเป็น `AUTHORING_DETAIL / REQUIREMENT_REVIEW`
- Evidence: ผู้ใช้กล่าว “โอเครครับ ลุย! อย่าลืมนะ เราเน้นให้ดูเข้าใจง่าย ถ้ามีข้อมูลเยอะๆ ช่วยออกแบบหน่อยว่าจะทำเป็นรูปแบบยังไงให้ user ใช้งานแล้วไม่งง”
- Decision: ทำ evidence C02 ต่อพร้อมจัดแบบ UX ที่ลดภาระการอ่านและช่วยหาข้อมูลที่ต้องกรอก; บันทึกแบบให้รีวิวก่อนลง product code
- Author proposal: หน้าเดียวแบ่งหมวดเดิม, ถามมี/ไม่มี/ยังไม่ทราบ, เปิดรายละเอียดเมื่อเกี่ยวข้อง, ภาพรวม→สิทธิแต่ละรายการ→วิธีคิด; ดู [UX draft](requirements/TGPS-C02-guided-rights-ux.md)
- Boundary: ผู้ใช้ยังไม่ได้อนุมัติ layout/interaction ที่เพิ่งร่าง; ไม่เปลี่ยน tax/readiness/coverage contracts, ไม่ปิด legal gatesหรือ acceptance, ไม่เริ่ม implementation planหรือเปลี่ยน C02 เป็น IN_PROGRESS

## DEC-021 — อนุมัติแบบ UX C02 และทำต้นแบบให้ลอง

- Date: `2026-10-22`
- Status: `AGREED` สำหรับ UX design v0.1 และดำเนินงานต่อ; parent legal evidence reviewยังOPEN
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังรับลิงก์ UX draftที่ reviewerตรวจแล้วและสรุปภาพรวม→สิทธิ→วิธีคิด, มี/ไม่มี/ยังไม่ทราบ และแยกกองทุนเดิม
- Decision: ใช้ [C02 UX design](requirements/TGPS-C02-guided-rights-ux.md) เป็นแบบหลัก; ทำต้นแบบสำหรับทดลองความเข้าใจจากข้อมูลสมมุติ และจัดfield/copy inventoryให้พร้อมรีวิวการเชื่อมต่อ
- Method: [standalone HTML preview](demo/c02-guided-rights-preview.html) เป็นdesign artifactในdocs ไม่เพิ่มrouteหรือเชื่อมHTTP calculationของdemo; local loopback previewเปิดเฉพาะไฟล์นี้
- Boundary: อนุมัติแบบไม่ใช่การรับงานหน้าจอที่สร้างใหม่หรือการรับรองกฎหมาย; C02 treatment implementationยังNOT_STARTED. ไม่สร้างC02 implementation planก่อนevidenceผ่าน, ไม่เปลี่ยน readiness/pack/catalog/API, ไม่mergeหรือpush. รูปแบบ prototypeไม่ใช่APIหรือvalidation contract

## DEC-022 — เสนอ C02A PVD กรณีพื้นฐานเป็นขั้นแรก

- Date: `2026-10-22`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW` — ยังไม่ได้รับอนุมัติstagedscopeนี้
- Evidence: ผู้ใช้สั่ง“โอเครครับ ลุย!”หลังรายการปิดกฎหมาย→เชื่อมC02; การตอบนี้อนุมัติให้ทำงานต่อในscopeเดิม ไม่ใช่อนุมัติการจำกัดREADYcoverageที่เพิ่งเสนอ
- Proposal: [C02A](requirements/TGPS-C02A-pvd-first-slice.md) เปิดbaselinePVDเฉพาะsingleemployer/singlefund/normalrate; positiveRMF/ESGและกรณีค้างยังปิดผล. PositivePVDแสดงภาษี/breakdownก่อน โดยส่วนทดลองเงินเพิ่มรอขั้นต่อไป; explicitPVDzeroคงsupportedbehaviorเดิมเมื่อfactsครบ
- Reason: บันทึกทางเดินที่รีวิวได้แทนค้นผลทั่วไปซ้ำแล้วเลื่อนgateโดยไม่มีหลักฐาน; [SETworkedexamples](policy-evidence/2026-10-22/README.md) เพิ่มcorroborationแต่ไม่ใช่RDlegalclosure
- Boundary: ไม่แทนที่DEC-019/parentrequirementจนuserอนุมัติ; ไม่มีproductcode/implementationplanหรือlegalacceptance. แม้อนุมัติscopeยังต้องreviewevidence/fixturesเฉพาะsliceก่อนimplement. คงUXที่อนุมัติและC01/F09/acceptanceเดิม

## DEC-023 — อนุมัติ C02A PVD กรณีพื้นฐานเป็นขั้นแรก

- Date: `2026-10-22`
- Status: `AGREED` สำหรับ staged scope; scoped evidence review ยัง OPEN
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังข้อเสนอให้เริ่ม PVD นายจ้างเดียวอัตราปกติ ปิดผลกรณีอื่นที่ยังไม่รองรับ และยังไม่เปิดทดลองเงินเพิ่มสำหรับ positive PVD
- Decision: อนุมัติ [C02A v0.1](requirements/TGPS-C02A-pvd-first-slice.md) ตามข้อเสนอ DEC-022; positive PVD เปิด baseline/breakdown เมื่อ facts และหลักฐานครบ ส่วน new-cash ปิดด้วย domain availability; explicit zero คง supported behavior เดิมเมื่อ facts ครบ
- Reason: เชื่อมงานจริงเป็นลำดับที่ตรวจได้ ขณะประเด็นหลายสิทธิ/ฐาน RMF ของ parent ยังต้องตรวจต่อ
- Boundary: เปลี่ยนสถานะข้อเสนอของ DEC-022 เป็น scope approved ตั้งแต่คำตอบนี้ ไม่แก้ประวัติเดิม; ไม่ถือเป็น legal certification, plan approval หรือ acceptance ของ implementation. ต้องปิด scoped evidence ก่อนสร้าง implementation plan; C02 parent, C01/F09, user visual acceptance ไม่เปลี่ยน ไม่มีสิทธิ push/merge เพิ่ม

## DEC-024 — Scoped C02A evidence เพียงพอสำหรับเขียนแผน

- Date: `2026-10-22`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW` — technical evidence disposition, ไม่ใช่ผู้ใช้อนุมัติแผน
- Evidence: [bounded review](policy-evidence/2026-10-22/c02a-scope/README.md), primary RD/SEC locators; independent reviewer ยืนยัน9/9และ chain/currency เพียงพอสำหรับ planning เมื่อบันทึก; ordinary reference ใหม่ตรวจ9/9
- Decision: gate ของ normal C02A เฉพาะการวางแผนเป็น ADEQUATE_FOR_PLANNING_ONLY; จัด [แผน4tasks](superpowers/plans/2026-10-22-c02a-normal-pvd.md) แบบ DRAFT_FOR_REVIEW ไม่ข้าม RED/GREEN หรือ pack/consumer review
- Reason: ปิดช่องว่างเฉพาะที่ต้องใช้โดยแยก actual-credit/normal-remittance facts และ corporate expense consequences; ไม่รอหรืออ้างว่าปิดกฎหมายทุกสิทธิของ parent แล้ว
- Boundary: C02 parent G1–G6 ไม่ถูกปิดรวม; ไม่รับรองกฎหมาย/ภาษี, ไม่ activate pack/catalog, ไม่เปลี่ยน runtime, ไม่ ACCEPTED. Plan review/execution choice ยัง pending ก่อน implementation

## DEC-025 — อนุมัติแผน C02A และเริ่ม Native execution

- Date: `2026-10-22`
- Status: `AGREED`
- Evidence: ผู้ใช้ตอบ “โอเครครับ ลุย!” หลังได้รับแผน4tasksและคำแนะนำNative
- Decision: อนุมัติแผน2026-10-22-c02a-normal-pvd และใช้Nativeตามคำแนะนำ; เริ่มIN_PROGRESS ผูกAC01–09
- Boundary: ไม่ขยายcoverage ไม่ถือว่าtests=ACCEPTED ไม่push/merge และคงC01/F09/parentC02เดิม

## DEC-026 — Commit/push C02A checkpoint and continue remaining verification

- Date: `2026-10-22`
- Status: `AGREED`
- Evidence: User instructed “commit and push แล้วทำที่เหลือต่อได้เลยครับ”.
- Decision: Commit and push scoped C02A work to the existing feature branch, then complete outstanding request-size/rendered verification and synchronize progress documents.
- Reason: Preserve the verified implementation before completing its remaining delivery checks.
- Boundary: No merge, force-push, Stage4 draft, new deduction treatment, or automatic user/legal acceptance. Parent C02 legal gates and C01/F09 remain open. New feature requirements still require review.

## DEC-027 — ข้อเสนอ C02B RMF ซื้อครั้งแรกโดยไม่มี PVD ร่วม

- Date: `2026-10-22`
- Status: `AUTHORING_DETAIL / REQUIREMENT_REVIEW` — staged scope ยังไม่อนุมัติ
- Evidence: ผู้ใช้สั่ง “โอเครครับ ลุย!” หลังรายงาน C02A delivery; อนุญาตให้ทำงานต่อใน roadmap แต่ไม่ได้เลือก staged RMF scope ที่เพิ่งเสนอ
- Proposal: [C02B v0.1-draft](requirements/TGPS-C02B-rmf-first-slice.md) เริ่ม own first-ever normal RMF purchases in2026, one fund/AMC, explicit noPVD/other rights/history; baseline-only สำหรับ positiveRMF. C02A positivePVD/RMFzero คงเดิม; combinedpositiveยังปิดผล
- Reason: [fact/time packet](policy-evidence/2026-10-22/rmf-facts-review/README.md) ทำ present facts/future obligations/AMC reporting ให้รีวิวแยกกันได้ ขณะที่ combined-PVD RMF base ยังไม่มี direct authority ที่เพียงพอ
- Boundary: ไม่แทน parent C02 approved scope หรืออนุมัติข้อจำกัดใหม่นี้แทนผู้ใช้; ไม่ปิด legal gates, ไม่กำหนด reporting-pending readiness, ไม่มี implementation plan/runtime changes. ต้องผ่าน scope/evidence/contract review ก่อน plan. C02A reduced-motion/user acceptance และ C01/F09 ไม่เปลี่ยน
