# C03 Annual Tax Estimate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task after plan approval. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ให้พนักงานประเมินภาษีทั้งปี 2569 จากยอดจริงและยอดคาด และดูยอดที่คาดว่าจะชำระเพิ่มหรือได้รับคืนเมื่อข้อมูลหัก ณ ที่จ่ายครบ

**Architecture:** บริการประมาณการใน domain ประเมินข้อเท็จจริงสองช่วงด้วยกฎ readiness ที่ใช้ร่วมกับ baseline เดิม แล้วส่งเฉพาะรายได้รวมและสิทธิที่ยืนยันเข้า `calculate_tax` เมื่อพร้อม Snapshot เก็บยอดแยกช่วงและผลจาก domain เดโมใช้ endpoint ประมาณการและระบบยกเลิกผลเดิมที่มีอยู่

**Tech Stack:** Python standard library, frozen dataclasses, `Money`/`Decimal`, pytest/Ruff/mypy และเดโม local HTTP กับ HTML/CSS/JS เดิม

**Spec:** [C03 v0.1](../../requirements/TGPS-C03-annual-tax-estimate.md), [DEC-034](../../DECISIONS.md#dec-034--c03-requirement-agreement-and-plan-review), [ตัวอย่างอ้างอิง AC01–09](../../implementation-reports/TGPS-C03-acceptance-reference.md)

**สถานะแผน:** `IMPLEMENTED` / Native ตาม DEC-035 · ตรวจในเครื่องตาม [DEC-036](../../DECISIONS.md#dec-036--c03-implementation-verified-locally) · User acceptance `OPEN`

## ข้อกำหนดร่วม

- ใช้ pack 2026 ที่ activate แล้วและ coverage เดิมของเงินเดือน, C02A หรือ C02B ยอดจ่ายสิทธิมาจากข้อเท็จจริงถึงวันตัดข้อมูลที่ผู้ใช้ระบุ ใช้เวอร์ชันเดิมของ rule pack, catalog และรูปแบบ snapshot ของ baseline
- ใช้ลำดับ `ADVANCED_TAX_PATH_REQUIRED → UNSUPPORTED → REQUIRES_INPUT → READY` แยก `None` จากศูนย์และแยกข้อผิดพลาดของข้อมูลจากการขอข้อมูลเพิ่ม ผลคำนวณและ export เปิดเมื่อ baseline `READY`
- ใช้ `Money` แบบ exact, typed immutable models, standard library และการคำนวณ deterministic เดโม loopback ใช้ allowlist และขอบเขต request เดิม ไม่มี storage หรือ log ข้อมูลการเงิน
- ผลและ error เป็นภาษาไทย ระบุชื่อรายการหรือช่องที่เกี่ยวข้อง และงดใส่ค่าที่กรอกใน error เกณฑ์ตรวจใช้ AC01–09 และ quality gates ตาม AGENTS §4 การรับงานผู้ใช้เป็นขั้นหลัง implementation

## จุดตรวจเพิ่มเติม

1. วันตัดใหม่แล้วเปลี่ยนกลับวันเดิมระหว่าง request ต้องยืนยันอีกครั้ง และคำตอบที่ค้างต้องเผยผลไม่ได้ (Task 3)
2. รายได้นอกขอบเขตที่ยืนยันในช่วงใดช่วงหนึ่งต้องมี precedence เหนือสิทธินอกขอบเขตและยอดเงินที่ว่าง โดยไม่ต้องสร้างยอดเงินมาแทนการยืนยัน (Task 1)
3. ฐานค่าจ้าง PVD ที่เกินยอดจริงแต่ต่ำกว่ายอดทั้งปีต้องเป็น field conflict รวมถึงเมื่อยอดคาดว่าง (Task 1)
4. PIT และยอดหักที่ใกล้กันอาจให้ส่วนต่างน้อยกว่าหนึ่งสตางค์ สถานะและข้อความบนจอต้องตรงกับค่าจริงใน snapshot (Tasks 1–3)
5. ย้ายยอดระหว่างสองช่วงแล้วผลรวมเท่าเดิมต้องเปลี่ยน snapshot และ replay ต้องปฏิเสธ payload ที่แก้แม้ใช้ hash เดิม (Task 2)

## สถานะความคืบหน้า

| Task | งาน | สถานะ |
| --- | --- | --- |
| 1 | Domain, readiness และยอดเพิ่มหรือคืน | เสร็จ · 43 tests ในชุดสุดท้าย |
| 2 | Snapshot, export และ replay | เสร็จ · 22 tests ในชุดสุดท้าย |
| 3 | HTTP และเดโมภาษาไทย | เสร็จ · 3 HTTP tests และ frontend 58/58 |
| 4 | ตรวจการทำงานรวมและเตรียมส่งรีวิว | เสร็จ · ผ่าน 7 gates, Chrome 1440/390 และ independent review fix pass |

## Task 1 — Domain และ readiness (AC01–08)

**ไฟล์:** สร้าง `src/tax_gps/calculation/annual_estimate.py` และ `tests/acceptance/test_c03_annual_estimate.py` ปรับ `src/tax_gps/calculation/readiness.py` เพื่อใช้การตรวจ coverage ร่วมกัน

**Interfaces ที่เสนอ**

- Frozen `EstimatePeriod(wages: Money | None, bonus: Money | None, withholding: Money | None, outside_coverage: bool | None)` สำหรับแต่ละช่วง
- Frozen `AnnualEstimateRights` ใช้ชนิดจาก `ExistingTaxBenefits` สำหรับ `parents`, `children`, `retirement_contributions`, `pvd`, `other_rights`, `fund_history`, `rmf` และให้ `personal_eligible`, `mortgage_eligible`, `social_security_paid`, `mortgage_interest_paid` รับ `None` ได้ เพื่อบอกข้อมูลที่ยังขาดก่อนประกอบ benefits สำหรับคำนวณ
- Frozen `AnnualEstimateInput(tax_year: TaxYear, cutoff_date: date | None, confirmed_for: date | None, actual: EstimatePeriod, forecast: EstimatePeriod, rights: AnnualEstimateRights, shared_limit_usage: tuple[SharedLimitUsage, ...] | None, pvd_forecast_single_employer: bool | None)` ใช้ `confirmed_for` เป็นหลักฐานยืนยันข้อมูลที่ผูกกับวันตัด ณ คำขอนั้น โดยรับจาก action ยืนยันของผู้ใช้ในเดโม
- `calculate_annual_estimate(inputs: AnnualEstimateInput, pack: ActivatedRulePack) -> AnnualEstimateResult` ให้ frozen result ที่มี `baseline: BaselineReadiness`, `tax: TaxState | None`, `settlement_status: TaxStatus`, `withholding_missing_fact_ids: tuple[str, ...]`, `annual_withholding: Money | None`, `settlement_kind: SettlementKind | None`, `settlement_amount: Money | None` โดย `SettlementKind` มี `PAY_MORE`, `REFUND`, `BALANCED` และ amount เป็นค่าบวกหรือศูนย์ `tax` มีได้เฉพาะ baseline `READY` สำหรับผลที่ baseline ยังไม่พร้อม ให้ `settlement_status` ตาม baseline และยอดที่คำนวณทั้งสองส่วนเป็น `None` กรณีข้อมูลขัดแย้งส่ง `AnnualEstimateInputError` พร้อม `fact_id` ที่กำหนดในโค้ด หรือใช้ `PvdWageBasisError` / `RmfFactConflictError` เดิม

- [x] เขียน `test_c03_wage_and_bonus_aggregation_and_forecast_edit`, `test_c03_unknown_income_is_not_explicit_zero`, `test_c03_withholding_status_and_exact_settlement` ผูกตัวอย่าง `BASE`, `BONUS-EDIT`, `BONUS-ZERO`, `WHT-*`, `FRACTION` ยืนยันรายได้รวมและ PIT เป็นค่าคงที่ตามตัวอย่าง การเปลี่ยนยอดหักไม่เปลี่ยน PIT และผลที่ readiness ปิดต้องมี `tax is None` และ `settlement_amount is None`
- [x] เขียน `test_c03_rights_and_status_precedence` และ `test_c03_cutoff_and_period_conflicts` ผูก `PVD`, `RMF`, `BLOCK-*`, `YEAR-END-*` ทดสอบ PVD true/false/unknown, RMF การประเมินต่างวันและ snapshot รายงานที่ไม่ตรง, สิทธินอก coverage, unknown แต่ละช่วง, ทั้งสองช่วงที่มีรายได้นอก coverage, วันที่ว่าง/ผิดปี, `confirmed_for` คนละวัน และค่า forecast บวกแต่ละช่อง ณ 31 ธ.ค. ทดสอบเงินผิดรูปแบบแยกจากเงินว่างที่ adapter ใน Task 3
- [x] รัน `uv run --locked pytest tests/acceptance/test_c03_annual_estimate.py -q` บันทึก RED ที่เกิดจากพฤติกรรมใหม่ กรณีที่ผ่านตั้งแต่แรกบันทึกเป็น characterization
- [x] แยกส่วนประเมิน coverage จาก `assess_baseline` เพื่อให้ทั้งสองเส้นทางใช้ logic เดียวกัน ส่วนที่ใช้ร่วมรับ facts PVD/RMF/สิทธิเดิม/ประวัติ/ครอบครัว/shared usage, ฐานรายได้สำหรับตรวจ PVD แบบ `Money | None`, ข้อบ่งชี้รายได้นอก coverage และ missing IDs ของเส้นทางนั้น เมื่อ C03 ยังขาดองค์ประกอบรายได้ ให้ขอข้อมูลโดยรักษา precedence จาก facts ที่ทราบ ห้ามประกอบ `IncomeProfile` ด้วยยอดสมมติ Legacy wrapper ส่งค่า gross และ material unsupported flag เดิม พร้อม signature, reason codes, output และ hash เดิม
- [x] ตรวจ PVD gross ด้วยเงินเดือนและโบนัสที่ได้รับจริงเมื่อทั้งสองยอดครบ ตรวจ rate ด้วยฐานค่าจ้างที่จ่ายจริงตามกติกาเดิม หาก PVD เป็นบวก ให้รวมคำตอบ `single_employer` ของช่วงจริงและสมมติฐานช่วงที่เหลือเป็นคำตอบทั้งปี ค่า false มีผล `UNSUPPORTED` และ unknown ที่ยังประเมินไม่ได้มีผล `REQUIRES_INPUT` ณ สิ้นปีใช้คำตอบของช่วงจริงที่ครอบคลุมทั้งปี กรณี RMF ใช้ `cutoff_date` ตรงกับ `assessment_date` และให้เงื่อนไขเดิมผ่านการตรวจของ domain
- [x] เมื่อครบและพร้อม ให้สร้าง `UserProfile` จากผลรวมทั้งสี่ช่องและเรียก `calculate_tax(profile, pack)` ครั้งเดียว เก็บข้อมูลหัก ณ ที่จ่ายแยกจากภาษีทั้งปี แสดง `None` พร้อม IDs เมื่อยอดหักขาด และคำนวณ `PIT − annual_withholding` ด้วย Money เมื่อครบ ใช้เครื่องหมายเลือก `SettlementKind` ก่อนส่ง `settlement_amount` เป็นขนาดของส่วนต่าง
- [x] รันคำสั่ง targeted อีกครั้ง จากนั้นรัน `uv run --locked pytest -q` และบันทึกหลักฐานใน ledger หากได้รับสิทธิ์ checkpoint ให้ใช้ `tgps-git` กับไฟล์ Task 1 เท่านั้น

## Task 2 — Snapshot และ replay (AC04, AC06, AC09)

**ไฟล์:** สร้าง `src/tax_gps/calculation/annual_estimate_audit.py` และ `tests/acceptance/test_c03_annual_estimate_audit.py` ใช้ `tax_gps.core.canonical` และ material ของ `TaxState` เดิม

**Interfaces ที่เสนอ**

- `create_annual_estimate_snapshot(inputs: AnnualEstimateInput, pack: ActivatedRulePack) -> AnnualEstimateSnapshot` คำนวณ authoritative result จาก inputs และ pack เดียวกัน Snapshot เป็น frozen object ที่มี result สำหรับ adapter และ `to_dict() -> dict[str, JsonValue]` สำหรับ export โดย material ภายในเป็น immutable
- `replay_annual_estimate(snapshot: Mapping[str, JsonValue], pack: ActivatedRulePack) -> AnnualEstimateResult` อ่าน snapshot ที่ถอดมาจาก JSON จับคู่เวอร์ชัน สร้าง typed inputs จาก material ของ snapshot และเทียบค่าที่คำนวณใหม่ Error ใช้ `AuditReplayError` แบบคงที่

- [x] เขียน `test_c03_snapshot_replays_complete_and_partial_withholding` และ `test_c03_snapshot_rejects_changed_material_or_version` ให้ round-trip ผ่าน canonical JSON ตรวจผลและ hash, baseline READY/settlement REQUIRES_INPUT กับ null และ missing IDs, ปฏิเสธ baseline ที่ยังไม่พร้อม และแก้วันตัด, ย้ายยอดข้ามช่วง, เปลี่ยน WHT หรือ material/outputs/pack/engine/schema แล้วต้อง replay ไม่ผ่าน ทดสอบค่า `FRACTION` เป็นสตริง Decimal แบบ exact
- [x] รัน `uv run --locked pytest tests/acceptance/test_c03_annual_estimate_audit.py -q` และบันทึก RED
- [x] สร้าง snapshot schema `tax-gps-annual-estimate/1` และระบุ engine version `ENGINE_VERSION`, pack ID/version/hash, material ทั้งสองช่วง, วันตัดและการยืนยัน, facts สิทธิและสมมติฐาน, ผล PIT/withholding/settlement และ provenance/trace จาก `TaxState` Hash material แบบ canonical ด้วย `sha256_hex` อ่าน material กลับเป็น typed inputs โดยคง null, Money input, ISO date และข้อเท็จจริงทั้งหมด จากนั้นใช้ผลที่คำนวณใหม่เทียบ canonical payload ทั้งชุดและ hash Archive เดิมใช้ replay แยกตาม engine/pack/schema ที่ตรง
- [x] รัน targeted tests และ `uv run --locked pytest -q` บันทึก ledger และทำ scoped checkpoint เมื่อได้รับสิทธิ์

## Task 3 — HTTP และเดโม (AC01–09)

**ไฟล์:** สร้าง `examples/annual_estimate_adapter.py`, `examples/web/annual-estimate.js`, `tests/acceptance/test_c03_annual_estimate_demo.py` ปรับ `examples/web_demo.py`, `examples/demo_profile.py`, `examples/demo_errors.py`, `examples/web/index.html`, `examples/web/app.js` และ CSS เดิมเฉพาะส่วนที่ใช้ร่วม เพิ่ม cases ใน `tests/web/test_app.cjs`

**Interfaces ที่เสนอ**

- `calculate_estimate(data: object) -> dict[str, object]` ที่ `POST /api/annual-estimate` รับ `cutoff_date`, `confirmed_for`, `actual`, `forecast`, `social_security`, `shared_usage`, `profile`, `pvd_forecast_single_employer` สองกลุ่มช่วงรับ `wages`, `bonus`, `withholding`, `outside_coverage` ค่า transport ใช้สตริง `""`, จำนวนเงิน หรือ `"true"`/`"false"` ในช่องที่ตรงชนิด `profile` ใช้เฉพาะ personal/mortgage, parents/children, retirement และ PVD/RMF/other rights/history ที่มีอยู่ `tax_year` มาจาก pack 2026
- HTTP 200 ให้ `baseline_status`, `reason_codes`, `missing_fact_ids`, `tax`, `settlement_status`, `withholding_missing_fact_ids`, `annual_withholding`, `settlement_kind`, `settlement_amount`, `export` ตาม domain `export` เป็น null เมื่อ baseline ยังไม่พร้อม HTTP 400 ใช้ error ที่ระบุ field สำหรับ transport หรือ domain input ที่ผิดรูป/ขัดแย้ง

- [x] เขียน `test_c03_http_partial_ready_and_raw_inputs_stay_private`, `test_c03_http_year_end_validation_and_existing_route`, `test_c03_http_real_route_and_body_limits` ตรวจผล `BASE`, `WHT-UNKNOWN`, `BLOCK-*`, `YEAR-END-*`, path เดิม และกติกา origin/host/body/header เมื่อเรียกทั้งสอง endpoint ตรวจ field IDs และ absence ของ input ใน error ตรวจว่า export partial เก็บ null ตามที่กำหนด
- [x] เพิ่ม browser cases `C03 shows three amounts and RMF conditions`, `C03 asks for reconfirmation after date edits`, `C03 rejects stale responses on edits or route switch`, `C03 displays a fractional result consistently`, `C03 handles year-end and missing withholding` ตรวจ FormData และพฤติกรรมกับ server ใหม่ ซ่อนผลก่อนหน้าและปิด download ทันทีเมื่อเปลี่ยนข้อมูล/โหมด ตรวจเปลี่ยนวันไปกลับ แล้วกด download ก่อน reconfirm ต้องไม่มี export และการแทนยอดสะสมด้วยยอดหนังสือรับรองช่วงเดียวกันคงมีช่อง actual เพียงชุดเดียว
- [x] รัน `uv run --locked pytest tests/acceptance/test_c03_annual_estimate_demo.py -q` และ `uv run --locked python -m examples.check_web_demo` บันทึก RED และ characterization ตามจริง
- [x] เพิ่ม route ใหม่ภายใต้การตรวจ loopback และ request size เดิม ใช้ตัว parse เงิน วันที่ boolean และ PVD/RMF เดิมร่วมกันตามที่รองรับ แยกการ parse facts ภาษีออกจาก `FinancialProfile` สำหรับ C03 แล้วให้ domain ตัดสิน coverage ทั้งสองช่วง ส่ง Thai field labels จาก code-owned IDs แยก wrong/empty และคง schema/HTTP behavior ของ `/api/calculate` พิสูจน์ด้วย regression test
- [x] เพิ่มตัวสลับ **ระบุรายได้ทั้งปี / ประมาณจากยอดจริงและยอดที่เหลือ** ในเดโมเดิม แสดงอินพุต actual/forecast และคำกำกับยอดสิทธิจริงถึงวันตัดข้อมูล ยืนยันกลุ่มข้อมูลสำหรับวันใหม่ด้วย control ที่มี label และ keyboard focus สร้าง `confirmed_for` เฉพาะเมื่อผู้ใช้ยืนยัน ล้างคำยืนยันและ published result เมื่อวันเปลี่ยน แม้สลับกลับวันเดิม ใช้ revision และ snapshot ของ request ที่มีอยู่เพื่อ deny คำตอบค้าง แสดง PIT, withholding และยอดเพิ่มหรือคืนก่อนรายละเอียดและ RMF conditions แสดงทศนิยมจาก canonical string โดยรักษาความหมายของส่วนต่างที่เล็กกว่าสตางค์ เมื่อไม่มี readiness ให้แสดงชื่อข้อมูลที่ขาดหรือรายการที่อยู่นอก coverage ผล C03 มีเฉพาะประมาณการและ export
- [x] รัน targeted, full pytest และ frontend runner เดิม บันทึกจำนวนและ AC ใน ledger ทำ scoped checkpoint เมื่อได้รับสิทธิ์

## Task 4 — ตรวจรวมและส่งรีวิว (AC01–09)

- [x] ตรวจเส้นทางเดิมและเส้นทาง C03 บน browser ที่เดสก์ท็อป/มือถือ พร้อม keyboard, การยกเลิกผล และ preference reduced motion ผูกหลักฐานกับ SHA และบันทึก browser/runtime จริง
- [x] รัน `tgps-verify` ครบ 7 คำสั่งตาม AGENTS §4 ตรวจ 100% statements/branches, frontend ใน server สด, build และ report failure/skip ตามจริง
- [x] เทียบผลกับ [ตารางอ้างอิง](../../implementation-reports/TGPS-C03-acceptance-reference.md) และ requirement ทีละ AC ตรวจ scope/version/privacy จาก diff แล้วขอ independent review ตามวิธี execution ที่ตกลง บันทึกผลและ rerun verification หลังแก้ไข
- [x] ใช้ `tgps-mark-progress` อัปเดต plan/ledger และใช้ `tgps-record-decision` เมื่อมีหลักฐานให้เปลี่ยนสถานะ อัปเดต README/Roadmap/requirement เมื่อถึง checkpoint ที่ตรงกับหลักฐาน ส่งผู้ใช้รีวิวก่อนบันทึก acceptance
