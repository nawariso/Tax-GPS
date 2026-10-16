---
name: tgps-verify
description: Run the full Tax GPS quality gates exactly as CI does (lint, format, strict mypy, 100% branch coverage, frontend lifecycle against a fresh server, build) and report real results. Use before claiming work is done, before committing, or when asked to check the project.
---

# tgps-verify

รันตามลำดับนี้ (ตรงกับ `.github/workflows/ci.yml`) และจดผลทุกขั้น ห้ามข้าม

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict
uv run --locked pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run --locked python -m examples.check_web_demo
uv build
```

## กติกา

- Frontend ตรวจผ่าน `examples.check_web_demo` เท่านั้น (เปิด server ใหม่) —
  `node tests/web/test_app.cjs` ตรงๆ อาจยิงไป server เก่าที่ค้างบน 8765
- Coverage ต้อง 100% statements/branches ของ `tax_gps`; เพิ่ม test ที่มีความหมายเท่านั้น
  ไม่ใช้ `pragma: no cover` เพื่อปิดช่อง
- ห้ามรัน `ruff format .` / `ruff check --fix` ทั้ง repo โดยไม่ตั้งใจ — จะ reformat งานคนอื่น
  แก้เฉพาะไฟล์ใน scope หรือถามผู้ใช้ก่อน
- บันทึก Python version จริงของเครื่อง (`uv run --locked python -VV`) แยกจาก CI 3.12

## รายงาน

| Gate | ผล |
| --- | --- |
| ruff check | N findings / clean |
| ruff format | N files / clean |
| mypy --strict | N errors / clean |
| pytest + coverage | N passed, coverage % |
| frontend | pass/total |
| build | ok / error |

gate ที่ไม่ผ่านให้บอกตามจริงว่าเป็นของงานนี้หรือค้างมาก่อน และใส่ใน ledger ผ่าน `tgps-mark-progress`
