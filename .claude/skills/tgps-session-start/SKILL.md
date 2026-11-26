---
name: tgps-session-start
description: Orient at the start of any Tax GPS session or handoff - read AGENTS.md, roadmap, decisions, active requirement/plan/ledger, check git state and run the baseline suite, then report where work stands. Use when starting work, resuming from another agent, or asked "ทำถึงไหนแล้ว".
---

# tgps-session-start

ทำทุกครั้งก่อนเริ่มงานใน session ใหม่ หรือเมื่อรับงานต่อจาก agent/model อื่น

## ขั้นตอน

1. อ่าน `AGENTS.md` ทั้งไฟล์
2. อ่าน `docs/ROADMAP.md` (บรรทัด `Current work` และตาราง §3) และ `docs/DECISIONS.md` (DEC ล่าสุด)
3. หา milestone ที่สถานะเป็น `IN_PROGRESS` แล้วเปิด:
   - requirement: `docs/requirements/<ID>-*.md`
   - plan: `docs/superpowers/plans/*<id>*.md` — ดูตาราง "สถานะความคืบหน้า" และ checkbox
   - ledger: `docs/implementation-reports/<ID>-progress.md`
4. ตรวจ git:
   ```console
   git status --short
   git log --oneline -10
   git diff --stat
   ```
   งานที่ยังไม่ commit อาจเป็นของคนอื่น ห้าม stash/reset/checkout ทับ
5. รัน baseline แล้วจดตัวเลข:
   ```console
   uv sync --locked
   uv run --locked pytest -q
   uv run --locked python -m examples.check_web_demo
   ```
   ถ้าต้องการภาพเต็ม รัน `tgps-verify`
6. เทียบเอกสารกับโค้ดจริง: ถ้า ledger/plan บอกว่า pending แต่ diff มีงานแล้ว (หรือกลับกัน)
   ให้รายงานความไม่ตรงนั้น

## รายงานให้ผู้ใช้ (ภาษาไทย)

- milestone/task ปัจจุบัน และสถานะแต่ละ task
- ผล test จริง (passed/failed พร้อมสาเหตุกลุ่มใหญ่)
- ความไม่สอดคล้องระหว่างเอกสารกับโค้ด
- ขั้นต่อไปที่แนะนำ แล้วรอผู้ใช้ยืนยันก่อนแก้โค้ด เว้นแต่ได้รับคำสั่งให้ทำต่อแล้ว
