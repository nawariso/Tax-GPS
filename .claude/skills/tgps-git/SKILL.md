---
name: tgps-git
description: Safe git workflow for Tax GPS - branch naming, scoped commits with conventional messages, what never to commit, and push/PR rules. Use whenever committing, pushing, branching or opening a PR.
---

# tgps-git

## Branch

- ห้าม commit ตรงบน `main`; branch: `feature/tgps-<milestone>-<slug>` (เช่น `feature/tgps-c01-baseline-integrity`)
- Merge เข้า `main` ผ่าน PR เท่านั้น CI (`.github/workflows/ci.yml`) รันบน PR/main

## ก่อน commit

1. `git status --short` และ `git diff --stat` — ดูทุกไฟล์ที่จะ commit
2. รัน `tgps-verify` (อย่างน้อย pytest + frontend) และบันทึกผลด้วย `tgps-mark-progress`
3. ถ้า gate ไม่ผ่าน ให้บอกใน commit body ว่าอะไรยังเปิดอยู่ อย่าอ้างว่าผ่าน

## Commit

- Stage ทีละไฟล์/กลุ่มที่ตั้งใจ (`git add <paths>`) ไม่ใช้ `git add -A` แบบไม่ดู
- Message: Conventional Commits ภาษาอังกฤษ
  ```text
  <type>(<scope>): <summary ≤ 72 chars>

  <what/why, acceptance IDs, verification results, known open items>
  ```
  type: `feat` `fix` `docs` `test` `refactor` `chore` `ci` · scope เช่น `candidate`, `demo`, `policy`, `c01`
- แยก commit ตามเรื่อง (โค้ดของ task / เอกสาร / agent tooling)
- ต่อท้ายด้วย attribution ที่เครื่องมือของคุณกำหนด (ถ้ามี)

## ห้าม commit

- `__pycache__/`, `.venv/`, `.coverage`, `dist/`, `tmp/`, cache ต่างๆ (ดู `.gitignore`)
- ข้อมูลการเงินจริงของผู้ใช้, secrets, ไฟล์ export JSON จาก demo
- ไฟล์ draft ที่ไม่เกี่ยวกับงาน (เช่น Stage 4 draft) เว้นแต่ผู้ใช้สั่ง

## ห้ามทำโดยไม่ถามผู้ใช้

- `push --force`, `reset --hard`, `rebase` ที่เขียนประวัติใหม่, ลบ branch
- `git stash` / `git checkout -- <file>` กับงานที่ยังไม่ commit
- `--no-verify` หรือข้าม hook
- Push/เปิด PR ครั้งแรกของงาน (ถามก่อนหนึ่งครั้ง เว้นแต่ผู้ใช้สั่งไว้แล้ว)

## หลัง push

- บันทึก commit SHA ใน ledger; ผล CI ต้องอ้าง SHA เดียวกันเท่านั้น
