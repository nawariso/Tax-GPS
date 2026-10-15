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
