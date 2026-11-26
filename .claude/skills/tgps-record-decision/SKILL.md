---
name: tgps-record-decision
description: Record an agreement or change in docs/DECISIONS.md (append-only), and sync the roadmap and affected requirement change logs. Use when the user agrees a direction, a milestone status changes, scope/order/contract changes, or work would go beyond the current requirement.
---

# tgps-record-decision

## เมื่อไหร่ต้องใช้

- ผู้ใช้ตกลงทิศทาง/ขอบเขต/ลำดับงานใหม่
- สถานะ milestone เปลี่ยน (เช่น REQUIREMENT_REVIEW → IN_PROGRESS → IMPLEMENTED)
- ต้องเปลี่ยนผลภาษี, ขอบเขตผู้ใช้, readiness, กติกาการใช้สิทธิ หรือสัญญา API
- ต้องการทำงานนอก requirement → **ถามผู้ใช้ก่อน** แล้วบันทึก

## รูปแบบ entry (เพิ่มท้าย `docs/DECISIONS.md`)

```markdown
## DEC-NNN — <หัวข้อสั้น>

- Date: `YYYY-MM-DD`
- Status: `AGREED` | `AUTHORING_DETAIL / REQUIREMENT_REVIEW`
- Decision: <ตัดสินใจอะไร>
- Evidence: <คำพูดผู้ใช้ที่ยกมาตรงๆ หรือหลักฐาน>
- Reason: <ทำไม>
- Boundary: <อะไรที่ decision นี้ไม่ได้ครอบคลุม>
```

## กติกา

- Append-only: ห้ามแก้ DEC เก่า ถ้าเปลี่ยนให้เพิ่ม DEC ใหม่และอ้าง DEC เดิม
- `AGREED` ใช้เฉพาะสิ่งที่ผู้ใช้ตกลงจริง; รายละเอียดที่ agent เสนอเป็น `AUTHORING_DETAIL`
- วันที่ใช้ Asia/Bangkok
- หลังเพิ่ม DEC: อัปเดต `docs/ROADMAP.md` (สถานะ + change log) และ change log ของ requirement ที่ได้รับผล
- ไม่เขียนประวัติใหม่ให้ดูเหมือนตกลงไว้ตั้งแต่แรก
