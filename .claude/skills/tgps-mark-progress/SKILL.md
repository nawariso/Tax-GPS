---
name: tgps-mark-progress
description: Mandatory after finishing any step - mark in the plan, ledger, requirement, roadmap and README what was done and how, with real evidence. Use every time a task step, fix, test run or doc change completes, before moving to the next task.
---

# tgps-mark-progress

ผู้ใช้กำหนด (DEC-009): **ทุกครั้งที่ทำอะไรเสร็จ ต้องทำเครื่องหมายในเอกสารว่าทำอะไรไปแล้วและทำอย่างไร**

## 1. Plan — `docs/superpowers/plans/<plan>.md`

- ตาราง "สถานะความคืบหน้า" ด้านบน: `✅ เสร็จ` · `🟡 บางส่วน — <ขาดอะไร>` · `⬜ ยังไม่เริ่ม`
- Checkbox:
  - เสร็จพร้อมหลักฐาน → `- [x]`
  - เริ่มแล้วไม่ครบ → `- [ ] **🟡 บางส่วน**`
- ใต้ checkbox เพิ่มบรรทัด:
  ```markdown
    ↳ ทำแล้ว: <ไฟล์/ฟังก์ชัน/test ที่แก้> — <ทำอย่างไร> — <ผลตัวเลขจริง>
  ```
- ถ้าบันทึกเดิมผิด ห้ามลบ ให้เพิ่ม `↳ แก้บันทึกเดิม: ...`

## 2. Ledger — `docs/implementation-reports/<ID>-progress.md`

- เพิ่ม bullet ตามเวลา: คำสั่งที่รัน, RED/GREEN counts, migration, ข้อจำกัดที่ยังไม่แก้
- อัปเดตบรรทัด `Task N: DONE | PARTIAL — ... | pending`
- ความผิดพลาด: ใช้ `~~ข้อความเดิม~~ **CORRECTION:** ...`

## 3. สถานะระดับ milestone (เมื่อเปลี่ยน)

- requirement header `Implementation: **...**` + แถวใน change log
- `docs/ROADMAP.md` บรรทัด `Current work` และตาราง §3 + change log
- `README.md` ส่วน Product roadmap
- ถ้าเปลี่ยนสถานะ milestone → `tgps-record-decision`

## กติกา

- เขียนเฉพาะสิ่งที่มีหลักฐานจริง (ตัวเลข test, path, commit) ไม่เขียนล่วงหน้า
- IN_PROGRESS/IMPLEMENTED ≠ ACCEPTED
- ทำก่อนไป task ถัดไป และก่อน commit
