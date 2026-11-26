# TGPS-C03 — Progress ledger

## 2026-11-25 — Requirement review / DEC-033

- [x] ตรวจ Roadmap, C01/C02A/C02B และ Product Review R04–R06 ที่ `1063fef` ก่อนร่าง Git มี Stage 4 draft เดิมอยู่เป็น untracked
- [x] บันทึก [DEC-033](../DECISIONS.md#dec-033--first-tax-estimate-mvp-coverage-and-c03-requirement-review) ใช้ coverage ที่รองรับอยู่เป็นฐาน MVP แรก และแยกกรณี PVD ร่วม RMF ไว้ทบทวนหลักฐาน อัปเดต Roadmap, C02 parent และ README การรับงาน C02A/C02B รอผลทดลองเดโม
- [x] จัด [ร่าง C03 v0.1](../requirements/TGPS-C03-annual-tax-estimate.md) พร้อม AC01–09 ออกแบบการกรอกยอดรวมสองช่วงและแยก readiness ของยอดชำระเพิ่มหรือคืนจาก baseline PIT
- [x] Builder check พบสี่ประเด็นและระบุคำตอบในร่างสำหรับรีวิว แยกคำยืนยันเงินได้นอก coverage สองช่วงและค่าจ้างที่รองรับ, ระบุผลของยอดหักว่างและยอดเกินช่วง ณ 31 ธ.ค., ตรวจฐานค่าจ้าง PVD กับรายได้จริงถึงวันตัดข้อมูล และให้ยืนยันสมมติฐานที่ใช้ทั้งปี เช่น นายจ้างเดียว
- [x] ตรวจแบบ ภ.ง.ด.91 ปี 2568 หน้า 2 และรายการแบบปี 2569 จากกรมสรรพากรโดยใช้แบบปีก่อนเป็นตัวอย่างโครงผลลัพธ์ ตรวจ SHA-256 ของ PDF เดิมด้วย Python หลัง `Get-FileHash` ใช้ไม่ได้ในรอบแรก
- [x] Baseline ก่อนร่างผ่านครบ 7 gates บน Windows Python 3.14.3 / Node 24.3.0. Python 814 ผ่าน (13.21s), coverage 3,175 statements และ 928 branches ที่ 100%, frontend 52/52 (fail 0, skip 0), lint/format/strict typing และ build 0.4.0 ผ่าน ผลชุดนี้เป็นหลักฐานของ source ที่มีอยู่
- [ ] Requirement review กับผู้ใช้ ข้อตัดสินเรื่องยอดจริงและสมมติฐานใหม่ยังเป็นข้อเสนอในร่าง
- [ ] Implementation plan, ตัวอย่างตัวเลขตรวจอิสระ และ AC-linked tests หลังรับ requirement

Current task: requirement draft ready for review. Implementation `NOT_STARTED`.

## 2026-11-25 — บันทึกพักงานและจุดรับช่วง

ผู้ใช้ขอให้บันทึกไว้เพื่อกลับมาทำต่อ หยุดที่ `REQUIREMENT_REVIEW` ของ C03 โดยมี [ร่าง v0.1 และเกณฑ์รับงาน AC01–09](../requirements/TGPS-C03-annual-tax-estimate.md) พร้อมให้รีวิว

1. เมื่อกลับมา ให้เริ่มรีวิวสองข้อในร่าง การแยกยอดจริงถึงวันตัดข้อมูลจากยอดคาดช่วงที่เหลือโดยใช้สิทธิที่จ่ายจริง และการแสดงภาษีทั้งปีเมื่อ baseline พร้อมแต่เว้นยอดเพิ่มหรือคืนถ้ายอดหัก ณ ที่จ่ายยังขาด
2. เมื่อรับ requirement แล้ว ให้บันทึกผลรีวิว จัดแผน C03 และเตรียมตัวอย่างคำนวณอิสระตามเกณฑ์รับงานก่อนเริ่ม implementation
3. การรับงาน C02A/C02B รอผลลองเดโม ส่วน PVD ร่วม RMF อยู่ระหว่างทบทวนหลักฐานตาม [DEC-033](../DECISIONS.md#dec-033--first-tax-estimate-mvp-coverage-and-c03-requirement-review)

- Git ณ จุดพักอยู่บน `feature/tgps-c01-baseline-integrity` ที่ `1063fef` เอกสาร C03 และรายการอัปเดต Roadmap/Decision Log อยู่ใน working tree สำหรับรีวิว Stage 4 draft ยังเป็นไฟล์ untracked แยกจากงานนี้
- ตรวจ baseline ก่อนพักครบ 7 gates ผ่านทั้งหมด Python 814 เทสต์ (13.01s), coverage 100% ทั้ง statements และ branches, frontend 52/52 โดยไม่มี fail หรือ skip, build 0.4.0 ผ่าน

## 2026-11-25 — กลับมาทบทวน requirement

- [x] เทียบร่าง C03 กับ Product Review R04–R06 และ `assess_baseline` ที่ `1063fef` ข้อเสนอที่นำมารีวิวคือใช้ยอดจริงถึงวันตัดข้อมูลแยกจากยอดคาดที่เหลือ ใช้เฉพาะยอดจ่ายสิทธิที่เกิดขึ้นแล้ว และแสดง PIT เมื่อ baseline พร้อมแม้ยอดหัก ณ ที่จ่ายยังขาด โดยเว้นยอดชำระเพิ่มหรือคืนและระบุช่องที่ขาด
- [x] ระบุจุดที่ต้องครอบคลุมในแผนหลังรับ requirement ตาม AC07 ปัจจุบัน `assess_baseline` รับรายการเงินได้นอกขอบเขตที่มียอดบวก ขณะที่ C03 เสนอคำตอบแยกสองช่วง การมีเงินได้นอกขอบเขตที่ผู้ใช้ยืนยันต้องไปถึง domain โดยไม่สร้างยอดเงินสมมติ และคำตอบยังไม่ทราบต้องแยกจากคำตอบไม่มี
- [x] ตรวจ baseline รอบรับช่วง `uv sync --locked`, `uv run --locked pytest -q` (814 ผ่านใน 13.08s) และ `uv run --locked python -m examples.check_web_demo` (52/52) จากนั้นตรวจครบ 7 gates บน Windows Python 3.14.3 / Node 24.3.0 ผ่านทั้งหมด Ruff format 198 ไฟล์, mypy 122 ไฟล์, pytest 814 ผ่านใน 13.56s, coverage 3,175 statements และ 928 branches ที่ 100%, frontend 52/52 (fail 0, skip 0) และ build 0.4.0
- [ ] ผู้ใช้รีวิวและยืนยันพฤติกรรม C03 ก่อนเขียนแผนและตัวอย่างตรวจอิสระ สถานะ `REQUIREMENT_REVIEW` / implementation `NOT_STARTED`

## 2026-11-25 — ยืนยันพฤติกรรมและจัดแผน / DEC-034

- [x] ผู้ใช้ตอบ “โอเครครับ เยี่ยมครับ ลุย!” ต่อการยืนยันสองข้อ บันทึก [DEC-034](../DECISIONS.md#dec-034--c03-requirement-agreement-and-plan-review) และซิงก์ requirement v0.1, Roadmap กับ README ให้แสดงว่าพฤติกรรมที่รีวิวตกลงแล้ว
- [x] จัด [แผน C03 สี่ tasks](../superpowers/plans/2026-11-25-c03-annual-tax-estimate.md) แบบ `DRAFT_FOR_REVIEW` ผูก AC01–09 กับ domain, snapshot/replay, HTTP/UI และการตรวจรวม ข้อเสนอแยกข้อมูลจริงและคาดไว้ใน snapshot ของ C03 และใช้ baseline engine/pack เดิม
- [x] จัด [ตัวอย่างอ้างอิง](TGPS-C03-acceptance-reference.md) คำนวณแยกด้วย Python `Decimal` แล้วเทียบ `calculate_tax` ที่ `1063fef` ทั้งหกรายการตรงกันทั้ง taxable และ PIT ตรวจส่วนต่างของยอดหักแยกและบันทึก expected statuses ของ AC01–09 ผลนี้เป็นหลักฐานอ้างอิงของ engine เดิม
- [x] รัน regression ชุด engine/PVD/RMF ผ่าน `uv run --locked pytest tests/acceptance/test_engine.py tests/acceptance/test_c02a_pvd.py tests/acceptance/test_c02b_rmf.py -q` ได้ 80 ผ่านใน 0.21s รอบก่อนหน้าที่เรียก Python ตรงจาก sandbox ออกด้วย exit 1 ตอน pytest เขียน `.pytest_cache` และยังนับเป็นผลผ่านไม่ได้
- [x] ตรวจระบบเดิมครบ 7 gates บน Windows Python 3.14.3 / Node 24.3.0 ผ่านทั้งหมด Ruff format 198 ไฟล์, mypy 122 ไฟล์, Python 814 ผ่านใน 13.25s, coverage 3,175 statements และ 928 branches ที่ 100%, frontend 52/52 (fail 0, skip 0) และ build 0.4.0
- [ ] รอรีวิวแผนเพื่อเริ่ม Task 1 ตาม RED → GREEN พฤติกรรมที่รีวิว `AGREED` · แผน `DRAFT_FOR_REVIEW` · implementation `NOT_STARTED`

## C03 Native execution / DEC-035

- [x] ผู้ใช้ยืนยันแผนและ Native execution ใช้ feature checkout เดิมที่ `1063fef` เพื่อรักษาเอกสาร C03 ที่อยู่ใน working tree ตรวจ baseline บน Windows Python 3.14.3 / Node 24.3.0 ได้ Python 814 ผ่านใน 12.54s และ frontend 52/52
- Pre-flight Task 1 → Task 2: ใช้ immutable `AnnualEstimateInput` และผล `AnnualEstimateResult` เป็น material ของ snapshot แยกจาก baseline audit เดิม
- Pre-flight Tasks 1–2 → Task 3: ใช้ result, readiness IDs และ export จาก backend สำหรับ render เงื่อนไขและปิดผลค้างในเดโม
- Ruling: การเว้นยอดเงินออมเกษียณเดิมเข้า readiness เป็น `retirement_usage` ที่ยังไม่ทราบผ่าน typed facts ของ C03 เพื่อจัด precedence โดยไม่เติมศูนย์ Legacy parser และผลเดิมใช้ contract เดิม
- Task 1 DONE (AC01–08): RED collection ขาดโมดูล `annual_estimate` → GREEN 41/41. รอบ typing แรกพบ test annotations และ identity chain ที่ไม่ตรง type แก้แล้ว mypy ผ่าน 124 ไฟล์ และ Python 855 ผ่านใน 13.24s, coverage 100% (3,291 statements/970 branches)

## 2026-11-26 — Implementation verification and review

- Task 2 DONE (AC04,06,09): RED collection ขาดโมดูล `annual_estimate_audit` → GREEN 20/20 รอบแรก ตรวจ replay ด้วย payload ที่ดาวน์โหลดและ pack/engine/schema ที่ตรงกัน แก้ type ของ RMF reporting และเพิ่ม regression จากรีวิว ได้ 22 tests ในชุดสุดท้าย
- Task 3 DONE (AC01–09): HTTP RED collection ขาด annual adapter และ frontend RED 5 จากเส้นทาง C03 ที่ยังไม่มี → HTTP GREEN 3/3 และ frontend GREEN 57/57 ก่อนรีวิว รอบ Ruff/mypy ชี้การนำเข้า fixture และการอ่านผลตอบกลับในเทสต์ แก้ทั้งสองจุดแล้ว
- Ruling: เก็บเด็กที่ยังไม่ยืนยันสิทธิเป็น missing fact ตามลำดับแถวของฟอร์มเพื่อให้ domain คง precedence เมื่อมีรายได้นอกขอบเขต แถวที่ยังรอยืนยันจึงยังไม่เข้าโครงสร้างสิทธิที่ใช้คำนวณ
- Independent review เทียบ working tree กับ `1063fef` พบสามข้อ แก้ในรอบเดียวและยืนยันจากเทสต์ที่เห็น fail ก่อนแก้ Python RED 2 สำหรับยอดกรอกละเอียดกว่าสตางค์ใน domain/replay และ frontend RED 2 สำหรับ RMF ที่แสดงทศนิยมต่างจาก export กับ PVD assumption ที่ค้าง หลังแก้ Python และ frontend ผ่านครบ
- Task 4 DONE: Windows Python 3.14.3 / Node 24.3.0 ผ่าน 7 gates Ruff ตรวจ 206 ไฟล์, mypy strict 128 ไฟล์, pytest 882 ผ่านใน 14.19s, coverage 3,394 statements และ 998 branches ที่ 100%, frontend 58/58 (0 fail, 0 skip), wheel และ sdist 0.4.0 สร้างได้
- Chrome headless 158.0.8127.37 เปิดเดโมจริงบน loopback พอร์ตว่าง ตรวจภาพ desktop 1440px และ mobile 390px โดยไม่มี horizontal overflow ใช้คีย์บอร์ดยืนยันวันที่และตรวจว่าการเปลี่ยนวันกลับเป็นวันเดิมยังต้องยืนยันใหม่ Desktop แสดง PIT 81,100.00 / หัก 75,000.00 / เพิ่ม 6,100.00 มือถือที่เว้นยอดหักช่วงที่เหลือยังเห็น PIT และบอกช่องที่ขาด ตรวจ reduced motion พบ animation ของยอดเป็น `none` การรัน harness แรกต้องตั้ง scenario ตัวอย่างก่อน การตรวจ viewport รอบถัดไปปรับการเทียบความกว้างเพื่อคิด scrollbar บน desktop
- หลักฐานผูกกับ working tree เหนือฐาน `1063fef` โดย SHA-256 ของ 17 ไฟล์ source/test ที่แก้หรือเพิ่ม `65b6917f1070c03c9e12f0223652d50d7866ef794c067ff273f5d3957ca5571e` (เรียงพาธ UTF-8 คั่นพาธและ bytes ด้วย NUL) Pack และ catalog ที่ออกแล้วไม่มี diff
- สถานะ `IMPLEMENTED` ตาม DEC-036 งานอยู่ใน feature working tree สำหรับรีวิว Remote CI และการรับงานผู้ใช้ยังเปิด
