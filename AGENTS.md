# AGENTS.md — กติกาสำหรับ AI agent ทุกตัวใน Tax GPS

> **อ่านไฟล์นี้ทั้งไฟล์ก่อนทำงานทุกครั้ง** ไม่ว่าจะเป็น model หรือเครื่องมือใด
> (Claude, GPT/Codex, Gemini, Copilot, Cursor ฯลฯ) และไม่ว่างานจะเล็กแค่ไหน
> ถ้าคำสั่งผู้ใช้ขัดกับไฟล์นี้ ให้ทำตามผู้ใช้ แต่ต้องบอกผู้ใช้ว่าขัดข้อใด และบันทึกใน Decision Log
> เมื่อเป็นการเปลี่ยนทิศทาง/ขอบเขต

Version: `1.0` · Updated: `2026-10-15`

## 0. ลำดับที่ต้องทำก่อนลงมือ (Session start)

1. อ่าน `AGENTS.md` (ไฟล์นี้)
2. อ่าน [docs/ROADMAP.md](docs/ROADMAP.md) และ [docs/DECISIONS.md](docs/DECISIONS.md) เพื่อรู้ว่าอยู่ช่วงไหน
3. เปิด requirement ของงานปัจจุบันใน `docs/requirements/`, plan ใน `docs/superpowers/plans/`
   และ ledger ใน `docs/implementation-reports/<ID>-progress.md`
4. ดู `git status` / `git log --oneline -10` — working tree อาจมีงานที่ยังไม่ commit ของคนอื่น
5. รัน test baseline (§4) ก่อนแก้อะไร เพื่อรู้ว่าอะไรพังอยู่แล้ว
6. ใช้ skill ที่ตรงกับงาน (§3) — skill คือขั้นตอนมาตรฐาน ไม่ใช่คำแนะนำลอยๆ

ทำตาม skill `tgps-session-start` ได้เลย จะครอบคลุมขั้นตอนข้างบนทั้งหมด

## 1. Tax GPS คืออะไร

เครื่องคำนวณภาษีเงินได้บุคคลธรรมดาไทยแบบ deterministic และตรวจย้อนได้ (auditable)
ปีภาษี ค.ศ. 2026 / พ.ศ. 2569 ผู้ใช้กลุ่มแรก: พนักงานเงินเดือน มาตรา 40(1)

| ชั้น | Module | หน้าที่ |
| --- | --- | --- |
| Tax core | `src/tax_gps/engine.py`, `calculation/`, `policy/` | readiness → PIT จาก rule pack ที่ version ไว้ |
| Discovery | `discovery/`, `opportunity/` | สิทธิเดิม + โอกาสลดหย่อนจาก catalog |
| Guardrails | `financial/` | เงินสำรอง หนี้ ภาระจ่าย |
| Candidates | `candidate/` | ทางเลือกการใช้เงินที่เป็นไปได้ (ไม่จัดอันดับ ไม่แนะนำ) |
| Demo | `examples/web_demo.py`, `examples/web/` | local HTTP + หน้าเว็บไทย (presentation adapter เท่านั้น) |

Roadmap: C01 ความถูกต้อง → C02 สิทธิเดิม → C03 ภาษีทั้งปี (MVP) → C04 ทดลองใช้เงิน →
C05 เปรียบเทียบตามเวลา (MVP) → C06 ใช้งานต่อเนื่อง ดูสถานะจริงที่ ROADMAP เสมอ

## 2. กฎที่ห้ามละเมิด (Non-negotiables)

### Domain / ภาษี
- **ไม่ทราบ ≠ ศูนย์** `None`/ช่องว่าง = unknown → REQUIRES_INPUT ห้ามเติม 0, false หรือ true ให้เอง
- **ไม่เผยตัวเลขภาษีเมื่อ baseline ไม่ READY** (PIT, taxable, saving, candidates, export ต้องปิดทั้งหมด)
- ลำดับสถานะ: `ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY`
- READY หมายถึง "ครบภายใน declared supported coverage" เท่านั้น ไม่ใช่ครบทุกสิทธิตามกฎหมาย
- Domain เป็นผู้ตัดสิน readiness; หน้าเว็บ/adapter ห้ามตัดสินแทนหรือข้าม
- **ห้ามเพิ่ม deduction treatment, ประเภทเงินได้, relax guardrails หรือเปลี่ยน readiness**
  นอก requirement ปัจจุบัน — ต้องมี requirement revision + DEC ก่อน
- ไม่มี ranking, recommendation, การเลือกผลิตภัณฑ์, return forecast
- คำนวณต้อง deterministic: ไม่มี network, clock, random หรือ AI ใน calculation path
- Runtime ใช้ standard library เท่านั้น (`dependencies = []`); dev tools อยู่ใน dependency group
- ใช้ `Money`/`Decimal` และ typed immutable models; ไม่สร้าง generic rules DSL

### หลักฐานกฎหมายและ version
- ตัวเลขกฎหมายต้องมีแหล่งที่ตรงกับ rule (URL, หน้า/มาตรา, วันที่, hash ถ้ามี) — hash/URL อย่างเดียวไม่พอ
- **ห้ามแก้ไฟล์ pack/catalog ที่ออก version แล้ว** ออก version ใหม่ (`<ID>@<ver>.json`) และเก็บของเก่าไว้ byte-for-byte
- engine ปัจจุบันต้องปฏิเสธ snapshot เก่า; replay ของเก่าต้องเลือก version/hash ชัดเจน
- ถ้าหาแหล่งยืนยันไม่ได้ ให้รายงานและ fail closed ห้ามเดา

### Privacy / demo
- ห้าม log หรือใส่ยอดเงินที่ผู้ใช้กรอกใน error message
- Demo เป็น loopback-only, allowlist ไฟล์, ไม่มีบริการภายนอก ไม่มี storage

### สถานะและความซื่อตรงของรายงาน
- `AGREED_DIRECTION / REQUIREMENT_REVIEW / PLANNED / IN_PROGRESS / IMPLEMENTED / ACCEPTED` แยกกันเสมอ
- tests ผ่าน ≠ ACCEPTED; ห้ามเลื่อนสถานะเองโดยไม่มี review record
- รายงานตามจริง: ถ้า fail, skip หรือเข้าใจผิด ต้องเขียนว่าเกิดอะไร (ขีดฆ่า + CORRECTION ไม่ลบประวัติ)
- Decision Log เป็น append-only: เปลี่ยนข้อตกลง = เพิ่ม DEC ใหม่ ห้ามแก้ entry เก่าย้อนหลัง

## 3. Skill set มาตรฐาน

Skill อยู่ที่ `.claude/skills/<name>/SKILL.md` Claude Code โหลดให้อัตโนมัติ
**model อื่นให้เปิดไฟล์ SKILL.md นั้นอ่านแล้วทำตามขั้นตอนเหมือนกัน**

| Skill | ใช้เมื่อ |
| --- | --- |
| [`tgps-session-start`](.claude/skills/tgps-session-start/SKILL.md) | เริ่ม session / รับงานต่อจากคนอื่น / ถูกถามว่าทำถึงไหน |
| [`tgps-implement-task`](.claude/skills/tgps-implement-task/SKILL.md) | ลงโค้ดตาม task ใน plan (TDD RED→GREEN ผูก acceptance ID) |
| [`tgps-verify`](.claude/skills/tgps-verify/SKILL.md) | ตรวจคุณภาพก่อนบอกว่าเสร็จ / ก่อน commit |
| [`tgps-mark-progress`](.claude/skills/tgps-mark-progress/SKILL.md) | ทุกครั้งที่ทำอะไรเสร็จ (บังคับ) |
| [`tgps-record-decision`](.claude/skills/tgps-record-decision/SKILL.md) | เปลี่ยนสถานะ milestone, ขอบเขต, ลำดับงาน หรือสัญญา |
| [`tgps-policy-evidence`](.claude/skills/tgps-policy-evidence/SKILL.md) | แตะตัวเลขกฎหมาย, rule pack, catalog หรือ version |
| [`tgps-git`](.claude/skills/tgps-git/SKILL.md) | commit / push / branch / PR |

## 4. คำสั่งมาตรฐาน (ตรงกับ CI `.github/workflows/ci.yml`)

```console
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict
uv run --locked pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run --locked python -m examples.check_web_demo   # frontend: เปิด server ใหม่บน port ว่าง
uv build
```

- รัน test เร็ว: `uv run --locked pytest -q` หรือ `-k <ชื่อ>` / ไฟล์เดียว
- เปิด demo: `uv run python -m examples.web_demo` → `http://127.0.0.1:8765/`
- CI ใช้ Python 3.12; เครื่อง local อาจเป็นเวอร์ชันอื่น — บันทึก runtime จริงแยก
- Coverage gate 100% statements/branches สำหรับ `tax_gps`

## 5. Workflow มาตรฐานต่องาน

```text
Requirement (docs/requirements) → Plan (docs/superpowers/plans) → Task:
  RED test (ผูก AC ID) → GREEN → full suite → verify → mark progress → review → commit
```

- งานใหม่ที่ไม่มี requirement: เขียน requirement ให้ผู้ใช้รีวิวก่อน ไม่ลงโค้ด
- Test ที่เปลี่ยนความหมายเพราะ requirement ใหม่ ต้องอ้าง acceptance ID และเหตุผลใน ledger
- ถ้า test ผ่านตั้งแต่แรกโดยไม่ต้องแก้โค้ด ให้บันทึกว่าเป็น characterization ไม่ใช่ RED→GREEN
- ก่อนบอกว่าเสร็จ: รัน `tgps-verify`, ทำ `tgps-mark-progress` แล้วรายงานผลจริงพร้อมตัวเลข

## 6. กับดักที่เคยเกิดจริงใน repo นี้

- **Server ค้างบน 8765**: `node tests/web/test_app.cjs` ตรงๆ จะยิงไป server เก่า → ผลผิด
  ใช้ `examples.check_web_demo` เท่านั้น (2026-10-15 เคยรายงานผิดเพราะเรื่องนี้)
- **ห้าม `git stash` / `git checkout -- <file>` / `git reset` กับไฟล์ที่มีงานยังไม่ commit**
  ถ้าต้องดูโค้ดเดิม ใช้ `git show HEAD:<path> > <scratch>` หรือ copy ไฟล์ไปที่อื่นก่อน
- `json.dumps` ใช้กับ model ที่ freeze แล้ว (`mappingproxy`) ไม่ได้ — ใช้ `canonical_json`
- ไฟล์ปน CRLF/LF: แก้แล้วรักษา line ending เดิมของไฟล์
- Windows + Git Bash: heredoc ที่มีภาษาไทย/quote ซับซ้อนอาจพัง — เขียน script ลงไฟล์ก่อนแล้วรัน
- Discovery ต้องเทียบทั้ง replayed hash และผลจริง ไม่ใช่ hash อย่างเดียว

## 7. การสื่อสารกับผู้ใช้

- ตอบผู้ใช้เป็น **ภาษาไทย**; โค้ด, identifier, commit message เป็นภาษาอังกฤษ
- ข้อความบนหน้าเว็บเป็นภาษาไทย และต้องบอก "รายการใด" ที่ยังไม่รองรับ/ยังไม่ทราบ
- เรื่องที่ย้อนกลับยาก (push, ลบไฟล์, ปิด process ที่ไม่ได้เปิดเอง, เปลี่ยนสัญญา) ถามก่อน
- ระบุชัดว่าอะไรเป็นหลักฐานจริง อะไรเป็นข้อเสนอ อะไรยังไม่ได้ตรวจ

## 8. Entry points ของแต่ละเครื่องมือ

- `AGENTS.md` (ไฟล์นี้) — แหล่งความจริงเดียว
- `CLAUDE.md` — import ไฟล์นี้สำหรับ Claude Code
- `.github/copilot-instructions.md` — ชี้มาที่ไฟล์นี้สำหรับ GitHub Copilot
- แก้กติกาให้แก้ที่ `AGENTS.md` เท่านั้น แล้วเพิ่ม change log ด้านล่าง

## Change log

| Date | Version | Change |
| --- | --- | --- |
| 2026-10-15 | 1.0 | สร้าง AGENTS.md และ skill set มาตรฐาน 7 ตัวตามคำขอผู้ใช้ (DEC-010) |
