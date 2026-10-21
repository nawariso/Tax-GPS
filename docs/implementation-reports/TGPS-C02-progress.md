# TGPS-C02 — Progress ledger

Requirement: [v0.1-draft](../requirements/TGPS-C02-existing-rights.md)

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
