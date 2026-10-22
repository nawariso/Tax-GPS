# C02A independent review and disposition

Date:2026-10-22 (Asia/Bangkok). Reviewer: `c02a_final_review`, fresh context,
read-only working-tree review against `1567e864`. No second reviewer was dispatched.
Scope: approved normal-PVD implementation, including untracked product/tests;
unrelated Stage4 draft excluded. Not legal certification or user acceptance.

## Findings and one fix pass

| Severity | Finding / effect | Disposition and actual evidence |
| --- | --- | --- |
| Important1 | Contradictory wage0 or wage>salary became generic profile error; user could not navigate to wage field | Fixed with code-owned PvdWageBasisError preserved at HTTP boundary as pvd.wage_basis, no submitted amount reflected. Two API tests and two frontend cases observed RED, then GREEN; final all-gates receipt below |
| Important2 | False PVD facts reused affirmative question labels, incorrectly saying normal/registered/single-employer cases were unsupported | Separate failure-case labels for all six false conditions, explaining prototype coverage. Six API cases observed RED then GREEN; actual browser normal_remittance=false displayed late/pause/defer reason |
| Minor3 | Request-size test does not yet measure representative complete Thai-name/record payload against4096 | Deferred minor; no proven over-limit ordinary request or weakened HTTP size rejection. Existing request limit remains4096. Explicit remaining Task3 verification work |

API regression run: **8 failed/2 passed →10 passed/0 failed**.
Frontend: **43 passed/2 failed →45 passed/0 failed**, skip0.
Full post-fix gates: [implementation verification](TGPS-C02A-implementation-verification.json)
—752 tests,2994statements/852branches100%, fresh-serverfrontend45/45,
ruffclean/177formatted/mypy114clean/build0.3.0. No second fix pass or rereview claim.

## Rulings on every declined-to-judge item

| Item | Executor ruling / cost if wrong |
| --- | --- |
| Legal certification/current amendment completeness | Bounded primary chain plus independent arithmetic supports declared slice; no certification asserted. New applicable evidence reopens policy review; wrong applicability risks wrong tax and requires versioned correction |
| Multiple employers/funds, exceptional rate, RMF/ESG, spouse rights | Stay named unsupported exactly as approved. Cost: these users cannot get a partial tax estimate from this slice |
| Actual credited paid0 with credited/remittance false | Zero path keeps approved positive-only restrictions; paid means actual credited money, not payroll withholding. Known current-year recapture/history remains separately required. Cost: unclear payroll reporting could mislead an answer, so actual-credit wording is explicit |
| Incomplete financial records in baseline-only | Keep validated debts/commitments/protection if submitted, as plan only exempts budget/assets/expenses. Cost: malformed irrelevant records can require correction before baseline display; no invented financial authority |
| Historical pack directly with current engine | Historical loader version/hash selection is supported; old engine emulation is not implemented and current snapshot rejects old engine version. Cost: archival recalculation needs matching historical engine |
| Python caller controls every dataclass/hash | Retain declared replay/material/hash boundaries; no sandbox against arbitrary in-process code. Cost: arbitrary Python callers are not untrusted web clients |
| LF-normalized history pins | Four pins compare HEAD content across Git checkout line endings; historical JSON files have no diff and were never written by these scripts. Cost: normalized tests alone do not prove raw filesystem line-ending identity |
| Package0.3.0/lock | Updated project version only, third-party dependencies unchanged; all standard gates and build passed afterward. Cost: consumers must account for changed material contracts |
| Test counts vs acceptance | Counts establish local technical checks only, not ACCEPTED. Cost: acceptance still needs separate review record |
| Rendered/keyboard/reduced motion | Actual Chrome1440/390/360/320 no overflow, synthetic normal/zero/missing/unsupported and Enter error focus checked. Fresh reduced-motion mode **UNVERIFIED**: exposed browser controls did not enable emulation (matchMedia false); prior UI02 runtime evidence is not relabeled as a fresh C02A pass. Cost: AC09 remains partial |
| Plan/ledger bookkeeping | Updated after observed results; two runtime tasks complete, Task3/4 remaining verification explicitly tracked. Cost: no complete-plan claim while those remain |
| C01/F09, parent C02, Stage4, push/merge | Unchanged; Stage4 left uncommitted, no push/merge/new remote CI. Cost: these earlier acceptance items remain open |

Other execution rulings retained in [progress](TGPS-C02A-progress.md): working in
existing feature checkout, native Windows bookkeeping, integrated Tasks2/3 before
Task1 full-suite green, and hidden obsolete aggregate field while explicit new
facts remain required. These do not relax domain readiness or privacy.
