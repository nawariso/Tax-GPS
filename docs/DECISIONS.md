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
