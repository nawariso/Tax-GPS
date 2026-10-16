---
name: tgps-policy-evidence
description: Verify Thai tax/legal sources and version rule packs or opportunity catalogs without overwriting history. Use when touching any legal number, source citation, src/tax_gps/policy/packs, src/tax_gps/opportunity/catalogs, loader version selection, or replay/hash behavior.
---

# tgps-policy-evidence

## หลักฐานกฎหมาย

1. ใช้แหล่ง primary ก่อน (ราชกิจจานุเบกษา, กรมสรรพากร, ก.ล.ต., สปส.) แล้วค่อย supplementary
2. ยืนยันว่า**เนื้อหา**ตรงกับ rule: หน้า/มาตรา/ข้อ, วันที่ลงนาม/ประกาศ/มีผล
3. บันทึกใน `docs/policy-evidence/<YYYY-MM-DD>/README.md`:
   URL, หน้า/ข้อ, วันที่, วิธีตรวจ, SHA-256 ของไฟล์ต้นฉบับ (ถ้าดาวน์โหลดได้), ข้อจำกัด
4. ตรวจว่าไฟล์ที่โหลดมาเป็นเอกสารจริง (เคยได้ PDF ที่ข้างในเป็นหน้า error)
5. ไม่พบหลักฐาน → ไม่เดา, ใส่ `null` แทนวันที่ที่ไม่รู้, รายงานและ fail closed

## Versioning artifacts

- ไฟล์ที่ออกแล้ว (`TH-PIT-2026-001.json` = 1.0.0, `...@1.0.1.json` ฯลฯ) **ห้ามแก้แม้ byte เดียว**
- เปลี่ยนเนื้อหา → ไฟล์ใหม่ `<ID>@<new-version>.json` และ:
  - อัปเดต `BUNDLED_*_VERSION_*` และชุด version ที่ loader รับใน
    `src/tax_gps/policy/loader.py` / `src/tax_gps/opportunity/loader.py`
  - loader ต้องปฏิเสธ version ที่ไม่รู้จัก และ `expected_hash` ที่ไม่ตรง
  - bump engine/consumer version ที่ผลลัพธ์ material เปลี่ยน
  - test: current โหลดได้, historical โหลดได้แบบระบุ version, engine ปัจจุบันปฏิเสธ snapshot เก่า
- Production candidate activation ผูกกับ catalog ปัจจุบันเท่านั้น
- Hash ใช้ `canonical_json` + `sha256_hex` จาก `tax_gps.core.canonical`

## บันทึก

- ใช้ `tgps-mark-progress` ใส่ source/hash/limitation ลง ledger
- เปลี่ยนตัวเลขกฎหมาย = เปลี่ยนสัญญา → `tgps-record-decision`
