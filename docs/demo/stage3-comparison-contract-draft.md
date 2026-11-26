# Stage 3 — User-controlled comparison contract

สถานะ: ผู้ใช้อนุมัติ scope สำหรับ presentation/demo implementation แล้ว
ยังไม่ใช่ independent acceptance หรือ production approval
ชื่อไฟล์เดิมคงไว้เพื่อรักษาลิงก์และตัวตนของร่างที่ผู้ใช้ตรวจ

ฐานที่ตรวจใน Git: `52f5bb24d360d0d1dfaf11f60ceedc10cf3fd907`
บน branch `feature/demo-stage2-profile` โดย working tree สะอาดก่อนสร้างเอกสารนี้

การอนุมัติในบทสนทนา: “อนุมัติ Stage 3 ตามร่าง และอนุญาตพัฒนาเดโมแยกระหว่างรอ gate เดิม”
ขอบเขต: ตารางเปรียบเทียบที่ผู้ใช้เลือกเอง ไม่จัดอันดับ ไม่แนะนำซื้อ
และคง independent acceptance/remote CI gate เดิม
เอกสารนี้ไม่ใช่ canonical requirement ของ P1-005 และไม่เปลี่ยนสถานะ P1-004

## 1. เป้าหมาย

ให้ผู้ใช้เลือกดูผลลัพธ์ที่ engine สร้างไว้แล้วแบบเคียงข้างกัน โดยเห็นชัดว่า
ภาษีที่ลดลง เงินที่ต้องจ่าย และสภาพคล่องที่เหลือเป็นคนละเรื่องกัน
ระบบไม่เลือกผู้ชนะ ไม่คำนวณคะแนน และไม่ตัดสินแทนผู้ใช้

## 2. สิ่งที่ผู้ใช้ทำได้

1. กรอกโปรไฟล์และคำนวณผ่านเส้นทาง Stage 2 เดิม
2. เปิดมุมมองตารางเปรียบเทียบจากผลคำนวณล่าสุดที่สำเร็จ
3. เลือกหรือยกเลิกเลือกรายการที่ต้องการนำมาเทียบจาก candidate ที่มีอยู่จริง
4. ดูผลของรายการที่เลือกเทียบกับ NO_ACTION ซึ่งแสดงเสมอ
5. เปิดรายละเอียดเงินจัดสรร เหตุผล ข้อจำกัดการถือครอง และหลักฐานผลคำนวณ
6. ดาวน์โหลดผล engine พร้อมข้อมูลว่าตนเลือกรายการใดมาแสดงในตาราง

ไม่มีรายการใช้เงินที่ถูกเลือกให้อัตโนมัติ NO_ACTION เป็นจุดอ้างอิงที่ตรึงไว้
ไม่ใช่คำแนะนำให้ทำหรือไม่ทำ ผู้ใช้ไม่ได้ส่งคำสั่งซื้อหรือคำสั่งลงทุนจากหน้าจอนี้

## 3. แหล่งข้อมูลที่เป็น authority

- รับ candidate จากผล `build_candidates` ผ่าน adapter เดิมเท่านั้น
- คงลำดับ NO_ACTION ก่อน แล้วตามลำดับ canonical ที่ engine ส่งมา
- ไม่เพิ่มจำนวนเงินทดลอง ไม่สร้าง candidate เพิ่ม ไม่ปรับ allocation และไม่เรียก optimizer
- ตารางแสดงเฉพาะ candidate ชุดปัจจุบัน ไม่อ้างว่าครอบคลุมทุกทางเลือกในตลาด
- ตารางไม่เปลี่ยน `src/tax_gps/`, policy, catalog, engine version หรือ core output hashes
- ใช้ข้อมูล opportunity จาก discovery/catalog ที่ผูกอยู่กับผลคำนวณเดียวกัน
  ไม่ join metadata จากคนละปี คนละ catalog หรือผลคำนวณเก่า

## 4. คอลัมน์เปรียบเทียบ

| สิ่งที่แสดง | ฟิลด์ authoritative | ความหมายบนหน้าจอ |
| --- | --- | --- |
| รายการ / จุดอ้างอิง | `candidate_id`, `allocations` | NO_ACTION หรือชื่อและเงินจัดสรรตาม opportunity ที่มีจริง |
| ภาษีก่อนใช้เงินเพิ่ม | `tax_before` | ภาษีตั้งต้นหลังสิทธิเดิม ไม่ใช่ยอดภาษีที่ต้องจ่ายสุทธิ |
| ภาษีหลังรายการนี้ | `tax_after` | ผลภาษีจาก engine โดยไม่หักภาษี ณ ที่จ่าย |
| ภาษีที่ลดลง | `tax_saved` | ไม่ใช่เงินสดที่ได้รับวันนี้ ไม่ใช่ผลตอบแทนลงทุน |
| เงินที่ต้องจ่ายเพิ่ม | `cash_outflow` | ไม่หักด้วย tax_saved เพื่อสร้างต้นทุนสุทธิสมมุติ |
| งบทดลองที่ยังไม่ใช้ | `unused_budget` | ไม่ใช่สภาพคล่องทั้งหมดที่ยังมีอยู่ |
| สภาพคล่องใช้เพิ่มที่เหลือ | `spendable_surplus_after` | หลังรักษาเงินสำรอง/ภาระจ่ายและหัก allocation ตาม engine |
| ช่องว่างความคุ้มครอง | `protection_gap` | แสดงตาม engine ไม่สมมุติว่าการลงทุนแก้ช่องว่างประกัน |
| เหตุผลและข้อจำกัด | `reason_codes` และ guardrails ของผลเดียวกัน | อธิบายสถานะ ไม่ใช้เป็นคะแนนหรืออันดับ |

จำนวนเงินใช้ค่า canonical จาก engine และจัดรูปแบบเพื่ออ่านเท่านั้น
ไม่มีการคำนวณภาษี สภาพคล่อง หรือสูตรเปรียบเทียบเพิ่มใน browser

## 5. การถือครองและข้อมูลที่ยังไม่ทราบ

- แสดง `lockup_metadata.minimum_holding_years` และ `measurement` ราย opportunity
  ตามข้อมูล discovery/catalog ที่ผลนี้ใช้ ไม่สร้างระยะถือครองรวมของ candidate
- หาก metadata ไม่ได้ระบุ ให้แสดงว่า “ไม่ระบุในข้อมูลที่ใช้” ไม่ใช่ “ไม่มีข้อผูกพัน”
- หากหนึ่ง candidate มีหลาย opportunity ให้แสดงข้อจำกัดแยกแต่ละรายการ
- `null` ของสภาพคล่องหรือความคุ้มครองแสดง “ยังไม่ทราบ” ไม่แปลงเป็นศูนย์
- ไม่มีการถาม tolerance แล้วตัดสินว่าเหมาะสม เพราะยังไม่มีสัญญาความเหมาะสมที่อนุมัติ
- ข้อมูล eligibility เป็น caller assertion ตาม Stage 2 ไม่ใช่การตรวจเอกสารหรือกฎหมาย

## 6. ไม่จัดอันดับและไม่ซ่อนผลที่ไม่น่าสนใจ

- ไม่มี best/recommended badge, winner, score, weights, objective, Pareto frontier,
  default sort ตามผลประหยัดภาษี หรือการเรียงตามความน่าสนใจ
- ไม่มีตัวกรองที่ตัด candidate ออกด้วย preference หรือเกณฑ์ใหม่ในรอบแรก
- รายการที่ภาษีไม่ลดลงยังเลือกดูได้ ถ้า engine สร้างไว้จริง
- ถ้ามีเฉพาะ NO_ACTION ให้แสดงจุดอ้างอิงกับเหตุผลจากผลเดิม
  ไม่สร้างทางเลือกใช้เงินเพื่อให้ตารางดูเต็ม
- รายการ `BLOCK` / `REQUIRE_REVIEW` / กฎยังไม่พร้อมไม่กลายเป็น selectable candidate
  ถ้าไม่มีอยู่ใน candidate output รายละเอียดข้อจำกัดยังดูได้ในมุมมองสิทธิเดิม
- เมื่อผลตัวเลขเท่ากัน คงลำดับ engine และแสดงข้อเท็จจริงเท่ากัน ไม่กำหนดผู้ชนะ

## 7. State และการป้องกันผลเก่า

- ก่อนมีผลสำเร็จ ไม่แสดงตารางที่ทำให้เข้าใจว่ามีผลคำนวณแล้ว
- การเลือก candidate เป็น presentation state ไม่เปลี่ยนผล engine
- เก็บ identity ของการเลือกโดยอ้างอิง `result_hash` และ `candidate_id` ร่วมกัน
  เพราะ candidate_id เดิมอาจปรากฏในผลของโปรไฟล์หรืองบต่างกันได้
- เปลี่ยน input, เพิ่ม/ลบ record, เปลี่ยนตัวอย่าง หรือคำนวณใหม่:
  ล้าง selection และ invalidate ตาราง/ข้อมูล export ก่อนรับผลใหม่
- แสดงผลใหม่แล้วเริ่มจาก NO_ACTION กับยังไม่มีรายการใช้เงินที่เลือก
- response เก่าทั้ง success/error/finally ต้องไม่ย้อนมาเปลี่ยนผลหรือ selection ล่าสุด
- หากคำนวณล้มเหลวหรือโปรไฟล์ไม่รองรับ ไม่ใช้ตารางเก่าแทนผลปัจจุบัน

## 8. Export และ privacy

- เก็บผล engine เดิมทั้งชุด ไม่เขียน comparison state เข้า canonical outcome material
  และไม่เปลี่ยน hash/version ของ core เพื่อรองรับหน้าจอ
- ข้อมูลรายการที่เลือกต้องอยู่ในส่วน presentation ที่แยกและระบุชัดว่าเป็นการเลือกของผู้ใช้
  ไม่ใช่ recommendation ของ engine; ชื่อ/โครงสร้าง envelope จะกำหนดในสเปก implementation
- อ้างอิงเฉพาะ candidate IDs ที่มีอยู่จริงในผลที่ export และผูกกับ result hash เดียวกัน
- เมื่อ input เปลี่ยนหรือผลไม่สำเร็จ ต้องดาวน์โหลดผลเก่าไม่ได้
- ยังไม่มี persistence, account, analytics, provider, upload หรือคำสั่งซื้อ
- JSON มีข้อมูลโปรไฟล์/การเงินตาม Stage 2; ต้องแจ้งก่อนดาวน์โหลดว่าไฟล์อาจมีข้อมูลส่วนบุคคล
  ห้ามใช้ไฟล์ข้อมูลจริงเป็นภาพหรือ fixture สำหรับ review โดยไม่ได้รับอนุญาต

## 9. Acceptance ที่เสนอสำหรับ implementation หลังอนุมัติ

| กรณี | เกณฑ์ผ่าน |
| --- | --- |
| เปิดผลครั้งแรก | NO_ACTION แสดงเสมอ; ไม่มีรายการใช้เงินถูกเลือกอัตโนมัติ |
| เลือก/ยกเลิกรายการ | ตารางแสดงตรงกับการเลือก; ไม่เปลี่ยน engine result/hash |
| ตรวจตัวเลข | ทุกช่องเท่ากับฟิลด์ authoritative ของ candidate เดียวกัน |
| คงลำดับ | ลำดับรายการที่เลือกเป็น subsequence ของลำดับ engine ไม่ใช่ลำดับที่คลิกหรือ tax_saved |
| NO_ACTION-only | แสดง baseline และเหตุผลจริง ไม่มี candidate แต่งขึ้น |
| ภาษีไม่ลดลง | candidate ที่มีจริงไม่ถูกซ่อนหรือประณามว่าเป็นทางเลือกผิด |
| Unknown | `null` คงเป็นยังไม่ทราบ และ metadata ที่ขาดไม่กลายเป็นไม่มีข้อจำกัด |
| หลาย opportunity | แจกแจง allocation/lockup แยกรายการ ไม่สร้างค่าเฉลี่ยหรือข้อผูกพันรวม |
| แก้ข้อมูล / เปลี่ยนตัวอย่าง | ล้าง selection ตาราง และ export เก่า; ผลใหม่ไม่รับ selection เก่าตาม ID อย่างเดียว |
| Response สลับลำดับ | ผลเก่าไม่ย้อนกลับมา และไม่ล้าง loading/selection ของคำขอล่าสุด |
| Export | ตัวเลข/hash ตรงผล engine; selection เป็น presentation ที่อ้าง candidate/result จริง |
| ความเข้าใจ | ไม่มี winner/ranking/recommendation และเห็นข้อความภาษีประหยัดไม่ใช่เงินสดทันที |
| Desktop/mobile | ตารางอ่านได้; หากต้อง scroll อยู่ในกรอบตาราง ไม่ทำให้ทั้งหน้าล้น |
| หลักฐาน | ทดสอบกับ HTTP/engine จริงและ browser จริง ไม่ใช้ API output ที่แต่งขึ้น |

หลัง implementation ต้องผ่าน locked install, lint/format, strict mypy,
full Python/JavaScript tests, core coverage threshold เดิม, build และ browser regression
จำนวน tests จะรายงานจากการรันจริง ไม่ถือว่าจำนวนจาก Stage 2 พิสูจน์ Stage 3

## 10. Gate และการอนุมัติ

การอนุมัติสัญญานี้อนุญาตเฉพาะ presentation/demo implementation
บน branch แยกตาม scope นี้ ไม่ใช่การรับรอง core หรือ production

- P1-004 independent acceptance ยัง pending
- Remote CI ของ Stage 2 ยัง UNVERIFIED ตาม [handoff](stage2-review.md)
- ไม่ merge, tag, release หรือเปิดใช้จริงด้วยการอนุมัติร่างนี้
- ไม่ตั้งชื่อร่างนี้เป็น approved P1-005 requirement โดยอัตโนมัติ
- กฎหมายล่าสุด การเลือกกองทุน ผลตอบแทน AI advice การเก็บข้อมูล และยื่นภาษีอยู่นอก scope

ได้รับอนุมัติจากผู้ใช้สำหรับสัญญานี้และข้อยกเว้นให้พัฒนาเดโม Stage 3
ระหว่างรอ gate เดิมแล้ว ถ้าต้องการ ranking/preference filter/recommendation ให้เปลี่ยนสัญญา
และอนุมัติกติกาใหม่ก่อน ไม่เพิ่มให้เองระหว่าง implementation

## เอกสารอ้างอิงภายใน

- [P1-004 requirement และ boundary](../requirements/TGPS-P1-004.md)
- [Stage 2 input contract](input-coverage.md)
- [Stage 2 review handoff](stage2-review.md)
- [`CandidateOutcome` / `CandidateResult`](../../src/tax_gps/candidate/models.py)
- [Catalog และ lockup metadata](../../src/tax_gps/opportunity/models.py)
