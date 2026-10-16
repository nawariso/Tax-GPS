---
name: tgps-implement-task
description: Implement one task from a Tax GPS plan with test-first RED→GREEN tied to acceptance IDs, preserving domain non-negotiables and existing uncommitted work. Use whenever writing or changing code under src/, examples/ or tests/ for a planned task.
---

# tgps-implement-task

## ก่อนเริ่ม

- มี requirement + plan task ที่ตกลงแล้วหรือยัง? ถ้าไม่มี → หยุด เขียน requirement ให้ผู้ใช้รีวิวก่อน
- อ่าน task ใน plan, acceptance IDs ที่เกี่ยวข้อง (เช่น `C01-AC09`) และ §2 ของ `AGENTS.md`
- ถ้างานต้องเพิ่ม deduction, เงินได้ประเภทใหม่, relax guardrail หรือเปลี่ยน readiness
  นอก requirement → หยุดและใช้ `tgps-record-decision`

## Loop ต่อ checkbox

1. **RED** — เขียน test ที่ระบุพฤติกรรมตาม AC (docstring หรือชื่อ test อ้าง AC ID)
   - ตรวจ machine fields (`code`, `status`, `reason_codes`, `missing_fact_ids`) ไม่ใช่ข้อความอย่างเดียว
   - ตรวจว่า error ไม่มียอดเงินที่ผู้ใช้กรอก
   - รัน test เป้าหมาย ต้องเห็น fail ด้วยเหตุผลที่คาด
   - ถ้าต้องพิสูจน์ RED กับโค้ดเดิม: `git show HEAD:<path> > <scratch>` แล้ว copy สลับ —
     **ห้าม `git stash`/`checkout`** กับไฟล์ที่มีงานค้าง
2. **GREEN** — แก้โค้ดน้อยที่สุดให้ผ่าน ตาม idiom เดิม (immutable dataclass, `Money`, pure function)
3. **Full suite** — `uv run --locked pytest -q` และถ้าแตะ `examples/web*` รัน
   `uv run --locked python -m examples.check_web_demo`
4. **บันทึก** — ใช้ `tgps-mark-progress` ใส่ตัวเลข RED/GREEN จริง

## ข้อควรระวัง

- Test เดิมที่ต้องเปลี่ยน: เปลี่ยนเฉพาะที่ความหมายเปลี่ยนตาม requirement และเขียนเหตุผลใน ledger
- Fixture ที่ "รู้ครบ" ต้องใส่ explicit zero/empty list เอง ห้ามให้ core เติม default zero
- Test ที่ผ่านทันทีโดยไม่แก้โค้ด = characterization ให้เขียนตามนั้น ไม่อ้างว่าเป็น RED→GREEN
- ถ้าพบ bug นอก task ให้จดใน ledger และบอกผู้ใช้ ไม่ขยาย scope เอง
- รักษา line ending (CRLF/LF) เดิมของแต่ละไฟล์
