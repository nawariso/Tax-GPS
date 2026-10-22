# C01 / UI01 checkpoint และ C02 draft

Date: `2026-10-15` (Asia/Bangkok)

## ทำแล้ว

- Code checkpoint: `4774983` — `feat(demo): finish baseline integrity and fintech restyle`
  บน `feature/tgps-c01-baseline-integrity`; parent `80afe5a`
- C01 Task1–5 และ fresh-review fixes IMPLEMENTED; F09 OPEN / acceptance conditional
- UI01 HTML/CSS restyle IMPLEMENTED; source review ไม่มี findings ที่ยืนยันได้
- ทุก quality gate ผ่าน Windows CPython3.14.3 และ isolated CPython3.12.14:
  695 tests ทั้งสอง runtime, frontend24/24, lint/format/strict mypy/build clean
- Coverage100%: Python3.14 = 2846 statements/798 branches;
  Python3.12 = 2863 statements/798 branches; ทั้งสองไม่มี misses
- Preview ตรวจซ้ำหลัง code commit: current asset bytes และ API smoke9/9
  ที่ http://127.0.0.1:64946/; server PID35652 ที่เปิดเองยังทำงาน
- C02 v0.1-draft REQUIREMENT_REVIEW, implementation NOT_STARTED;
  fresh builder check “nothing important left” นอก legal/approval gates ที่ระบุ

หลักฐานคำสั่ง/runtime/output และ code-diff fingerprint:
[verification JSON](TGPS-handoff-verification.json).
ร่าง C02: [requirement](../requirements/TGPS-C02-existing-rights.md) /
[ledger](TGPS-C02-progress.md).

## ยังไม่ผ่าน / ยังไม่ทำ

- Rendered1440/390/360, Thai clipping/overflow, real keyboard focus/scroll และ
  reference similarity: UNVERIFIED เพราะ CUA apps=[]/browsers=[]
- F09 historical WinError10053 ยังไม่ reproduce; ไม่สร้างหลักฐานใหม่หรือปิดเอง
- Remote GitHub Actions ยังไม่รัน; localWindows/Node24.3.0 ไม่ใช่ Ubuntu/Node22
- ยังไม่ push/เปิด PR/merge; workflow รันเฉพาะ push main หรือ PR main
  จึงต้องขออนุญาต push branch/เปิด draft PR เพื่อรัน remote CI
- C02 ต้องให้ผู้ใช้รีวิว requirement, ปิด evidence matrix/independent fixtures
  แล้วเขียน implementation plan ก่อนเพิ่ม treatment ใหม่

## วิธีที่ใช้แทนและการเก็บประวัติ

ใช้ isolated tmp/ci312-venv เพื่อทดสอบ Python3.12 โดยไม่เปลี่ยน default .venv3.14
และไม่อ้างว่าแทน remote CI ได้ครบ. เก็บ code checkpoint เดียวสำหรับ C01/UI01
เพราะทั้งสองมี regression ใน acceptance file เดียวกันและผ่าน review รวมแล้ว;
แยกเอกสารเป็นอีก commit. ไม่เปลี่ยน released JSON ไม่รวม unrelated Stage4 draft,
ไม่ stash/reset/overwrite งานเดิม. หลัง verification เปลี่ยนเฉพาะเอกสาร
จึงไม่รัน full suite ซ้ำโดยไม่มี code change

## Draft PR ที่เตรียมไว้ (ยังไม่ได้ส่ง)

Title: `Complete C01 baseline integrity and UI01 fintech restyle`

Base: `main`; head: `feature/tgps-c01-baseline-integrity`; draft: true

Incomplete tax facts now propagate domain readiness through calculation, discovery,
candidates and demo errors without exposing usable tax output. Invalid input reports
safe code-owned fields rather than reflecting arbitrary input. Version guards preserve
explicit current/historical replay boundaries. The local Thai calculator also gains
the approved cream/forest presentation with native links into its existing controls.

Validation: Windows CPython3.14.3 and isolated3.12.14 each pass695 tests, 100% core
statement/branch coverage, fresh-server frontend24/24 and lint/format/mypy/build.
C01 F09 remains OPEN, rendered visual acceptance is pending and remote CI is not yet
verified. C02 is documentation for requirement review only; it adds no treatment.
This draft does not request merge or imply milestone acceptance.

## Remote follow-up — หลังผู้ใช้อนุญาต

- [x] Push head c4527c9e2a2c3b041ff72e96ac5f404c06a94170 และเปิด
  [draft PR#4](https://github.com/nawariso/Tax-GPS/pull/4), ยังไม่ merge
- [x] [CI run10](https://github.com/nawariso/Tax-GPS/actions/runs/38765573860)
  SUCCESS: Ubuntu24.04.5/Python3.12.15/Node22.23.3, Python695,
  100% statements/branches, frontend24/24, lint/format/mypy/build ผ่านทั้งหมด
- [x] ตรวจ log ว่า checkout merge-ref b9015a3ba9103664a2d143ec40677e029ab81214
  ของ head ข้างต้นจริง; [evidence](TGPS-remote-ci.json) ไม่กล่าวอ้างผลนี้กับ head ใหม่
- [ ] F09 และ rendered visual acceptance ยังคงเปิด; C02 ยังคง REQUIREMENT_REVIEW

ข้อความ “ยังไม่ push/remote CI ยังไม่รัน” ข้างบนเป็นสถานะ ณ checkpoint เดิม
เพิ่ม follow-up นี้โดยไม่ลบประวัติ. Commit ต่อจากนี้บันทึกเอกสารล้วน;
จะตรวจ CI ของ head ที่อัปเดตแยกก่อนรายงานผลสุดท้าย

## จุดรับช่วง 2026-10-16 — กลับมาทำต่อจากตรงนี้

ผู้ใช้ขอให้โน้ตงานไว้แล้ว commit/push บน branch เดิม;
ไม่มีการอนุมัติ merge หรือเปลี่ยนสถานะ acceptance ในคำสั่งนี้

- [x] C01 Task 1–5 IMPLEMENTED แล้ว ไม่ต้องเริ่ม implementation เดิมซ้ำ
- [x] UI01 restyle IMPLEMENTED แล้ว
- [ ] ตรวจ rendered UI ที่ 1440/390/360px: ภาษาไทยล้น/ถูกตัด, scroll,
  keyboard focus และความใกล้เคียง reference; ยังไม่มี visual acceptance
- [ ] รีวิวรับงาน C01 โดยรักษา F09 OPEN / acceptance conditional:
  WinError10053 เดิมยัง reproduce ไม่ได้; probes ที่ผ่านไม่ยืนยันสาเหตุเดิม
- [ ] รีวิว C02 v0.1-draft กับผู้ใช้ → legal evidence matrix + independent
  numeric fixtures → implementation plan → RED/GREEN; ลำดับเสนอ PVD → RMF → Thai ESG
  ห้ามเพิ่ม treatment/readiness ก่อนผ่าน requirement/evidence gates
- [ ] C03–C06 ยังไม่เริ่ม; MVP ดูภาษีทั้งปีอยู่ปลาย C03

Baseline สดรอบสรุปสถานะ: Python695 ผ่านใน10.47s, fresh-server frontend24/24
ไม่มี fail/skip. ผล full gates ก่อน checkpoint บันทึกใน C01 ledger.
เอกสาร remote-CI เดิมอ้าง head c4527c9 เท่านั้น ไม่ใช่ผล CI ของ checkpoint ใหม่นี้.
คง Stage4 draft ที่ไม่เกี่ยวข้องไว้นอก commit. เริ่ม session ถัดไปด้วย
`tgps-session-start` แล้วตรวจ Git/CI ของ SHA ปัจจุบันก่อนกล่าวอ้างผลใหม่.

## ตรวจสถานะ 2026-10-20 — ยังไม่เริ่ม implementation เพิ่ม

- [x] อ่าน roadmap/decisions, C01/UI01 plans/review/ledgers และ C02 draft/ledger;
  จุดรับช่วงยังเป็น visual review, C01 acceptance/F09 และ C02 requirement/evidence gates
- [x] Baseline บน HEAD `da8e5c9`, Windows Python3.14.3 / Node24.3.0:
  `uv sync --locked` ผ่าน; `uv run --locked pytest -q` = 695 passed ใน10.37s;
  `uv run --locked python -m examples.check_web_demo` = 24 passed, 0 failed/skip
- uv sync ครั้งแรกติดสิทธิ์อ่าน cache นอก workspace; รันซ้ำด้วย escalation แล้วผ่าน
- รอบนี้ไม่ได้รัน coverage/lint/format/mypy/build หรือ remote CI ซ้ำ;
  remote evidence เดิมอ้าง head c4527c9 เท่านั้น ไม่ใช่สถานะ GitHub ปัจจุบัน
- Git diff c4527c9..da8e5c9 เป็นเอกสารเท่านั้น; ก่อนบันทึกรอบนี้ working tree
  มี untracked `docs/demo/stage4-local-profile-contract-draft.md` ซึ่งคงไว้ตามเดิม
- ไม่มี product-code edits, commit/push/merge หรือการเปลี่ยนสถานะ acceptance;
  ขั้นถัดไปที่เสนอคือ rendered UI review ก่อน แล้ว C01/F09 review และ C02 ตาม gates

### UI01 follow-up หลังผู้ใช้สั่งทำต่อ

- [x] Chrome rendered1440/390/360, keyboard focus/CTA/skip link/table scroll และ
  Thai/default/error views ตรวจแล้ว; แก้ mobile overflow จากจุดวงจรตกแต่งหนึ่งจุด
- [x] Full local gates: Python695/11.61s, coverage100%2846/798, frontend24/24,
  lint/format148/mypy102/buildผ่าน; fresh source review0findings
- [ ] Reduced-motion-mode rendered check และ user visual acceptance ยังค้าง;
  C01 acceptance/F09 และ C02 requirement/evidence gates ไม่เปลี่ยน
- หลักฐาน/ภาพ/ข้อจำกัดอยู่ใน [UI01 rendered report](TGPS-UI01-visual-review-2026-10-20.md).
  Preview ใหม่ http://127.0.0.1:57955/ (serverของsessionนี้); คืน viewport/default sampleแล้ว.
  ยังไม่มีcommit/push/merge; Stage4 draft คงเดิม

## Checkpoint / CI — 2026-10-21

- [x] UI02 reduced-motion runtime checked, media/default restored; see UI02 follow-up report.
- [x] Code `805e2d9` and documentation `951732e` committed and pushed to the existing feature branch/draft PR4 under DEC-018; no merge.
- [x] Remote run13 `39628740428` SUCCESS for head951732e / mergec404f7a, Ubuntu24.04.5/Python3.12.15/Node22.23.3: Python695, coverage100%, frontend37/37, all gates pass. Evidence: TGPS-UI02-remote-ci-2026-10-21.json. A later receipt commit needs its own CI result.
- [x] C01 executor acceptance handoff review and C02 scope review brief prepared; no new legal certification or treatment.
- [ ] User visual acceptance, independent C01 acceptance/F09 disposition, C02 detailed requirement approval then evidence/fixture gates. C02 implementation NOT_STARTED.
- Unrelated untracked Stage4 draft preserved and excluded from commits.
