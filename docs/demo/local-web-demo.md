# Tax GPS — ทดลองหน้าจอที่เชื่อม engine จริง

Status: LOCAL DEMO, not a production release. P1-004 independent acceptance remains pending.
The UI is separately authorized by the request to visualize actual use; it does not expand
P1-004's domain scope, select a winner, or authorize a later recommendation phase.

## เปิดใช้งาน

รันจาก root ของ repository:

```console
uv sync --locked
uv run python -m examples.web_demo
```

เปิด http://127.0.0.1:8765/ ใน browser บนเครื่องเดียวกัน หยุดด้วย Ctrl+C
ถ้า port ถูกใช้อยู่ ให้รัน `uv run python -m examples.web_demo --port 8766`
แล้วเปิด http://127.0.0.1:8766/

ตัวเดโมไม่อยู่ใน wheel ของ core ต้องใช้ source checkout ที่มี `examples/`
ไม่ต้องติดตั้ง Node, web framework, frontend build tool หรือ runtime dependency เพิ่ม

## สิ่งที่ลองได้

1. กรอกเงินเดือนทั้งปี ประกันสังคมที่จ่ายแล้ว สินทรัพย์สภาพคล่อง
   ค่าใช้จ่ายจำเป็นต่อเดือน และงบที่ต้องการทดลอง
2. กดคำนวณ เพื่อดูภาษีปัจจุบันและเงินที่ใช้เพิ่มได้หลังกันเงินตาม financial policy
3. เปรียบเทียบ NO_ACTION กับทางเลือกที่ engine สร้าง:
   ภาษีหลังจัดสรร ภาษีที่ลดลง เงินจ่ายเพิ่ม งบที่ไม่ใช้ และสภาพคล่องที่เหลือ
4. สลับไปดูสิทธิและเงื่อนไข พร้อมสถานะที่ยังไม่พร้อม กฎและ source IDs
5. เปิดรายละเอียด hash หรือดาวน์โหลด JSON ผลคำนวณ

มีสถานการณ์สำเร็จรูป 4 แบบ: มีสภาพคล่อง, สภาพคล่องจำกัด,
ยังไม่ทราบสินทรัพย์สภาพคล่อง, และฐานภาษีต่ำจนไม่มีผลประหยัดภาษี
กรณีสุดท้ายตั้งใจแสดงว่าการใช้เงินไม่จำเป็นต้องให้ประโยชน์ภาษี

## ขอบเขตและสมมุติฐานที่แสดงบนหน้าจอ

- เงินได้จากเงินเดือน 40(1) ปี 2026 / พ.ศ. 2569 เท่านั้น
- เข้าเงื่อนไขสิทธิส่วนตัว ไม่มีหนี้ ไม่มีภาระเงินสดผูกพัน ไม่มีสิทธิบิดามารดา/บุตร/
  ดอกเบี้ยบ้าน/เงินสะสมเกษียณในตัว adapter นี้ ความคุ้มครองประกันยังไม่ทราบ
- ช่องวงเงินกลุ่ม Thai ESG / ESGX ที่ใช้ไปแล้วเป็นข้อมูลตรวจความจุร่วม ไม่ใช่รายการ
  ลดหย่อนใหม่ในฐานภาษีเริ่มต้น หากมีประวัติการใช้สิทธิจริง ต้องใช้โปรไฟล์เต็มที่รองรับ
  ก่อนนำไปเป็นเครื่องมือสำหรับข้อมูลจริง
- เว้นสินทรัพย์หรือวงเงินร่วมว่าง = unknown ไม่ใช่ 0
- ไม่มีการหักภาษี ณ ที่จ่าย ไม่มีจำนวนเงินคืน/ภาษีต้องชำระสุทธิ ไม่มีการยื่นแบบ
- ไม่มีอันดับ คำแนะนำซื้อ/ขาย ผลตอบแทนคาดการณ์ หรือการเลือกกองทุน
- ไม่เปลี่ยนกฎที่อยู่ใน engine และไม่ตรวจยืนยันกฎหมายล่าสุดใหม่
  ศิลปะและ Solar Rooftop ที่ catalog ระบุ RULE_NOT_READY ยังคงไม่เปิดใช้
- ภาษีที่ลดลงคำนวณจาก PIT ก่อนลบ PIT หลัง ไม่ใช่คูณ marginal rate
  และไม่บวกเป็นเงินสดคืนเข้าสภาพคล่อง

## ผลตัวอย่างที่รันจริง

Input: salary 990,500; social security 10,500; assets 500,000;
monthly essential expenses 50,000; budget 100,000; shared usage 0;
planning date 2026-10-14.

| ผลลัพธ์ (บาท) | ไม่ใช้เงินเพิ่ม | จัดสรร 100,000 |
|---|---:|---:|
| ภาษีเงินได้ | 79,000 | 60,500 |
| ภาษีลดลง | 0 | 18,500 |
| เงินจ่ายเพิ่ม | 0 | 100,000 |
| สภาพคล่องใช้เพิ่มที่เหลือ | 350,000 | 250,000 |

เมื่อเปลี่ยน assets เป็น 200,000 ทางเลือกใช้เงินเพิ่มถูกจำกัดเหลือ 50,000:
ภาษีหลังจัดสรร 69,000; ภาษีลดลง 10,000; spendable surplus หลังจัดสรร 0.

## ความเป็นส่วนตัวและการเปิด server

ฟังเฉพาะ 127.0.0.1 ไม่เปิดสู่ LAN หรือ Internet ตรวจ Host/Origin ของ request
ไม่เก็บข้อมูลลง database หรือ browser storage ไม่บันทึก request log และไม่มีบริการ
ภายนอก/analytics/font CDN เปิดไฟล์ได้เฉพาะ asset ที่ระบุไว้ ไม่เปิด root repository

ไฟล์ JSON ที่ผู้ใช้กดดาวน์โหลดมีข้อมูลการเงินและผลคำนวณ เก็บไว้ในที่ปลอดภัย
standard-library HTTP server นี้สำหรับ local demo เท่านั้น ไม่ใช่ deployment architecture
และไม่มีระบบ authentication / TLS / production operational controls

## การตรวจสอบ

```console
uv run pytest tests/acceptance/test_web_demo.py -q
uv run python -m examples.check_web_demo
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv build
```

Local checkpoint verification: 25 Python demo tests; 633 total Python tests passed,
plus 5 JavaScript lifecycle regression tests using real HTTP/engine responses.
Strict mypy includes `examples/`. The frontend check requires Node.js 22+ only for
verification; running the demo itself still needs only Python and uv. Its helper starts
an isolated loopback server on an ephemeral port and shuts it down afterward.

The lifecycle tests cover out-of-order success, an older request finishing while the
newest is pending, an older transport failure, invalid input, and editing displayed inputs.
Only DOM behavior and response timing are controlled; tax results come from the real engine.
The demo CI workflow now includes this check, but remote execution remains UNVERIFIED.

Core package `tax_gps` retains 100% statement and branch coverage; this coverage figure
is not a claim of 100% coverage for the demo HTTP adapter or JavaScript.

Browser verification exercised all four scenarios, editing a budget to 25,000,
invalid-input handling with old results hidden, recovery, both result views, audit disclosure,
and an actual JSON download whose result hash matched the displayed one.
Desktop and mobile widths 390 / 360 showed no page-level horizontal overflow.

Generated local evidence (Git-ignored, illustrative inputs only):

- `examples/artifacts/browser-checks.json`
- `examples/artifacts/desktop.png`
- `examples/artifacts/mobile.png`
- `examples/artifacts/tax-gps-demo-2026.json`

These artifacts are local evidence, not fixtures consumed by the demo. A clean clone has no
screenshots until browser verification is repeated. Remote CI for these demo changes is
UNVERIFIED; existing P1-004 review/merge gates are unchanged.
