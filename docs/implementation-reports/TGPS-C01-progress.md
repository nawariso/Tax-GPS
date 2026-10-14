# SDD ledger — plan: docs/superpowers/plans/2026-10-15-c01-baseline-integrity.md

Spec: TGPS-C01 v0.1. User authorized implementation after receiving the detailed requirement links.

- Workspace: current checkout, branch feature/tgps-c01-baseline-integrity. Preserve unrelated pre-existing Stage 4 draft.
- Execution: inline, native Windows commands; persistent ledger replaces POSIX task helper tooling.
- Pre-flight: Task 1 TaxState evidence → Task 2 discovery/HTTP; Task 3 bundle selection → all fixtures and Task 2; Task 4 response handling → Task 2 envelopes. No conflicting interfaces.
- Baseline: uv sync --locked succeeded; uv run --locked pytest -q → 650 passed.
- Task 1 RED: new baseline suite → 13 failed / 1 passed (missing readiness/evidence and unrecognized pool acceptance).
- Task 1 GREEN: new baseline suite → 14 passed after readiness/core/discovery evidence changes.
- Migration: explicit zero added only to known-complete salary/artwork/solar fixtures; positive prior usage/retirement expectations changed to blocked baseline, with standalone capacity math retained.
- Task 1/2 integrity finding: discovery compared carried output_hash only. New real test changed PIT with unchanged hash → FAILED (DID NOT RAISE); compare both replayed hash and material output. Cost if omitted: stale tax amounts could accompany a valid-looking hash.
- Task 1: integration verification in progress.
- Resume 2026-10-15: full suite was 224 failed / 449 passed. Single cause: test catalog helper serialized `catalog_to_dict` (frozen mappingproxy) with json.dumps. Helper now reads the raw current 1.0.1 catalog resource → 673 passed.
- Open after resume: ~~Node `tests/web/test_app.cjs` 21/23 (demo still returns 200)~~ **CORRECTION:** this run hit a stale server already listening on 127.0.0.1:8765 (PID 12788, pre-change code). Via `examples.check_web_demo` (fresh server) the suite was already 23/23. Rule: verify frontend only through `uv run --locked python -m examples.check_web_demo`. ruff 32 findings, ruff format 17 files, mypy 3 errors — all in uncommitted C01 work; deferred to Task 2/5.
- Task 2/3 note: partial uncommitted work exists (web demo/JS RED tests; versioned 1.0.1 pack/catalog, loader version/hash selectors, policy-evidence record).
- Task 1: DONE (Python suite 673 passed). Lint/format/mypy findings carried to Task 5.
- Task 2: DONE. Added: 7 structured extended-profile error cases (AC09/AC11); 2 `build_candidates` non-READY rejections isolated from the profile-hash check (AC09); READY copy scope test. RED→GREEN shown for: scoped error text/missing ids (frontend 21/23 → 23/23), READY exclusions copy (1 failed → passed). Unknown retirement/other income now carry reason codes. Python 683 passed; frontend 23/23.
- Task 2 known limitations (not fixed): parser-level REQUIRES_INPUT uses code `INPUT_REQUIRED` while domain uses `BASELINE_NOT_READY`; some missing ids are prose (`personal eligibility`, `mandatory payment`); unknown commitment `mandatory` is tagged `ELIGIBILITY_REQUIRED`; generic INVALID_INPUT no longer names the malformed amount field.
- Task 5 drift to fix: README and `docs/demo/input-coverage.md` still describe shared usage as a capacity fact only / retirement blocked by the demo; behavior now comes from the domain.
- Process note: during Task 2 a `git stash push examples/demo_profile.py` was run by mistake and immediately restored with `git stash pop`; diff verified intact.
- Task 3: PARTIAL — evidence record, 1.0.1 resources, loader selectors, version tests present.
- Task 4: PARTIAL — `Connection: close`, `_discard_rejected_body` and a rejected-POST test exist; diagnosis evidence (repetition counts/runtimes) still missing.
- Task 5: pending.
