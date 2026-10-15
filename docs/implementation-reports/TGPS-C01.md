# TGPS-C01 implementation report

Date: 2026-10-15 (Asia/Bangkok). Requirement: TGPS-C01 v0.1.
Implementation: **IMPLEMENTED** — Task 1–5 including final review fix-pass verified locally.
Independent milestone acceptance: **NOT ACCEPTED**; F09 remains **OPEN / conditional**.

## Revision and scope

Pre-C01 artifact: `de85aee67e3da34e6a83c296ad88d6e377f0858a`.
Resumed HEAD: `80afe5a`; prior implementation `6428809`, tracking `2cc5dca`.
This report includes the current uncommitted working-tree changes on
`feature/tgps-c01-baseline-integrity`. No commit, push, merge or remote CI is claimed
for these changes. The unrelated Stage 4 draft was preserved.

Core readiness gates supported salary calculations before publication. Positive retirement
or prior shared usage blocks the baseline; unknown material facts require input.
Discovery propagates reasons and missing facts, candidates reject closed baselines,
and the demo invalidates old results, selections and export on edits/errors/late responses.
Current artifact selectors preserve explicit historical versions without granting current
allocation authority. No deduction category, income scope or financial guardrail was added.

## Acceptance evidence

Paths below are relative to the repository root. Tests are real domain/HTTP/lifecycle
checks; passing them does not establish independent legal or milestone acceptance.

| AC | Evidence | Result |
| --- | --- | --- |
| AC01 | `test_baseline_integrity.py::test_known_zero_preserves_independent_salary_golden`; salary 990500, SSO 10500 → taxable 820000, PIT 79000, saving 18500 | PASS |
| AC02 | `test_engine.py` low-income golden; `test_zero_value_serialization.py`; supported 300000 salary → taxable 129500, PIT numeric zero | PASS |
| AC03 | `test_baseline_integrity.py::test_incomplete_baseline_cannot_publish_tax_or_impact`; RMF/PVD positive → UNSUPPORTED with null tax, guarded tax impact | PASS |
| AC04 | `test_known_zero_preserves_independent_salary_golden`; zero retirement preserves baseline | PASS |
| AC05 | Baseline suite positive prior usage, capacity-authority and HTTP/frontend tests | PASS |
| AC06 | Baseline suite unknown / explicit zero / complete empty list; unknown never becomes zero | PASS |
| AC07 | Parent unknown/false/true tests; confirmed parent taxable 790000, PIT 73000 | PASS |
| AC08 | `test_combined_material_findings_have_stable_precedence_and_all_reasons` | PASS |
| AC09 | Discovery evidence, candidate activation/build closed-baseline rejection, structured HTTP errors | PASS |
| AC10 | Fresh-server frontend 24 cases, including prior/unknown usage invalidating tax, selection and export; late response/old selector cannot restore | PASS |
| AC11 | Legacy request tests in `test_web_demo.py`; extended-profile matrix in `test_demo_profile.py` | PASS |
| AC12 | Negative/malformed/unknown pool tests; unknown pool rejected even at zero | PASS |
| AC13 | `test_c01_artifact_versions.py`: source metadata, selectors/hashes, historical catalog and DRAFT policy rejection; evidence notes below | PASS with SEC raw-file hash limitation |
| AC14 | Supported tax/discovery/candidate determinism and audit replay suites; readiness/reasons/scope in material hashes | PASS |
| AC15 | Current tax/discovery/candidate engines reject old engine labels; explicit historical artifact loads; real archived old-core replay below | PASS |
| AC16 | HTTP Host/Origin/framing/size/private-path suite; ten narrow repeats; 100 old + 100 current socket probes | Investigation complete; F09 OPEN, acceptance conditional |
| AC17 | Existing financial/guardrail acceptance suites on READY salary tax | PASS |
| AC18 | Existing family/mortgage/PIT-boundary golden and negative tests | PASS |

Test files are under `tests/acceptance/`; frontend cases are `tests/web/test_app.cjs`,
run only through `uv run --locked python -m examples.check_web_demo` on a fresh port.

## Migration and versions

| Artifact / consumer | Historical | Current |
| --- | --- | --- |
| Rule pack / opportunity catalog | 1.0.0 unsuffixed JSON | 1.0.1 version-suffixed JSON |
| Core engine / package distribution | 0.1.1 | 0.2.0 |
| Discovery / candidate engine | historical code in pre-C01 Git artifact | 0.3.0 |
| Allocation policy | historical contract | 1.0.1 |

Legacy `OpportunityFacts()` defaults to unknown shared usage and now returns
REQUIRES_INPUT. Callers may supply `shared_limit_usage=()` only when the complete list
is known to contain no usage; this is not a default repair. The README example and
known-complete fixtures now declare it explicitly. Positive retirement/shared-usage
profiles previously displaying incomplete results now return UNSUPPORTED. Unknown parent
eligibility returns REQUIRES_INPUT. Existing supported golden tax values are unchanged.

Non-READY serialized tax outputs retain null PIT/taxable/marginal values with
`reason_codes`, `missing_fact_ids`, `calculation_scope`. Discovery carries
`baseline_status`, `baseline_reason_codes`, `missing_fact_ids`. Parser-level missing
input uses `INPUT_REQUIRED`; domain baseline rejection uses `BASELINE_NOT_READY`.
Both expose structured status/reasons and hide tax/results/export. They are distinct
failure layers; consumers must handle both.

Released pack/catalog JSON was not edited in this continuation. Unsuffixed 1.0.0 raw
bytes match pre-C01 commit exactly:

- pack SHA-256: `593ada7f90289adeb941599bf043f25f9d5dad1e4f87a8e95c371fc2b1ef839f`
- catalog SHA-256: `1c2bc2d38e682eea6412f825096a407b980415fbafd8d9d9223b10993cee814d`

These are file-byte hashes; canonical activated content hashes are a separate identity.
Loaders accept explicit `version="1.0.0"` and optional `expected_hash`, reject unknown
versions/hash mismatches, and default to 1.0.1. Current allocation activation compares
the accepted current catalog's content and hash, so a historical catalog cannot become
current production authority even when it loads successfully.

## Historical replay and methods retained

The matching old engine artifact is retained in Git commit
`de85aee67e3da34e6a83c296ad88d6e377f0858a`; use its source and lockfile together.
It was extracted with `git archive` into ignored `tmp/c01-history`, without stash,
checkout/reset, switching HEAD or replacing current working files. A separate process
loaded archived `src` plus archived examples. Core 0.1.1, pack/catalog 1.0.0 replayed the
synthetic salary profile with PIT 79000 and output hash
`ef38a41f9760e1272a486c1daecc6731055722e232d0532f9a668476c4482650`.
The same profile's omitted usage now intentionally yields null PIT under current code.

Exact reproducible scratch scripts, runtime and socket probe method are preserved in
[HTTP diagnosis](TGPS-C01-http-diagnosis.md), with [raw results](TGPS-C01-http-evidence.json).
Do not make a current engine impersonate an old version by passing an old label.
No new compatibility engine was created. Inline native Windows commands and this tracked
[progress ledger](TGPS-C01-progress.md) replace the plan's POSIX bookkeeping helpers.

Task 3 historical catalog rejection already existed despite a pending checkbox; it was
confirmed and extended as characterization. New tests for engine-label impersonation
actually failed (2 failed / 6 passed) before guards were added; full suite then 685 passed.
Three dead discovery branches were removed under the existing public READY invariant,
with unchanged public regression expectations. Additional activation rejection tests
passed immediately and are characterized honestly, not claimed as RED→GREEN.

## Policy evidence

[Evidence record](../policy-evidence/2026-10-15/README.md) maps the SSO wage-base rule
to [Royal Gazette printed pages 5–6, clause 3(1)](https://ratchakitcha.soc.go.th/documents/98728.pdf)
and the 2026 pool to [SEC Q&A page 1 table / page 2 question 4](https://www.sec.or.th/TH/Documents/Thai%20ESGX/QA-LTF-to-Thai%20ESGX-010468.pdf).
Source text was retrieved again in this session; existing numerical policy is unchanged.
The saved Gazette PDF SHA-256 is in the evidence record. SEC raw PDF download/checksum
remains unavailable; no raw-file checksum or original publication timestamp is invented.
This is scoped corroboration of the changed source records, not a review of all Thai law.
Artwork/solar rules remain closed where authoritative material conditions are unresolved.

## HTTP diagnosis and remaining limitations

F09's exact WinError 10053 was not reproduced. Old/current controlled probes delivered
all 403 responses; the measurable difference is unread old request bodies versus drained
bounded current bodies. Existing HTTP regression passed ten independent pytest invocations.
The causal explanation for the original intermittent transport failure remains unproven.
This investigation is complete as required by the conditional reporting path in §8,
but F09 remains OPEN and C01 must not be accepted unconditionally from these results.

The fresh review identified the earlier parser field/row-identity limitation and raw
parent identity reflection as Important; both were fixed in one RED→GREEN pass. Scalar
IDs are now canonical, repeated flags include record indices, and standard parent roles
use allowlisted IDs while arbitrary labels use parent[index].eligible. INVALID_INPUT
amount errors identify their code-owned field, and constructor errors retain a safe
record/profile scope. Unknown non-parent booleans retain generic ELIGIBILITY_REQUIRED
with an exact missing field path; no unknown is normalized or tax published.
No new browser visual/manual layout review was performed in this continuation; automated
frontend lifecycle uses actual HTTP/engine results. Remote CI and Python 3.12 execution
are unverified for this working tree; local runtime is CPython 3.14.3 on Windows 11.

## Verification and review

Actual gate history and final fresh-review disposition follow below.
Initial verification failed honestly: lint 36, format 17 files, mypy 3 errors; coverage
99.78%, then 99.95% because the DRAFT allocation activation rejection was untested.
One verification attempt also found unformatted Python blocks in the new diagnosis
Markdown; only that new file was formatted. These failures are preserved in the ledger.

Before-review local gates: sync/lint/format/strict mypy all clean; 686 Python tests passed
in 9.12s, 2842 statements / 796 branches with zero misses (100%). Frontend 23/23
passed; sdist and wheel 0.2.0 built. Exact commands/output/exit codes are retained
in [before-review evidence](TGPS-C01-verification-before-review.json). The helper initially used
Windows cp874 for Node output and failed decoding/printing its checkmark; frontend
itself exited 0. Helper switched to UTF-8 and resumed only outstanding gates.

Code diff fingerprint (git diff de85aee -- src examples tests pyproject.toml uv.lock):
`b1f2dbf2b71f1c44a24adbd18267adc22ef1412f09f3d8bfbf99b46a24b22bda`.


## Final review and completion record

Fresh read-only reviewer `c01_final_review` found two Important issues and no Critical/Minor:
generic malformed HTTP errors and repeated unknown flags lacked usable identity; arbitrary
parent labels reflected raw input in parser/domain errors. Both were reproduced by new
failing tests, then fixed. Eight targeted Python regressions passed; real frontend test
went from 23 pass / 1 fail to 24/24. Full Python suite 694 passed in 9.92s; final coverage
run 694 passed in 10.51s, **2846 statements / 798 branches, zero misses, 100%**.
Locked sync, lint, format (139 files), strict mypy (102 files), frontend 24/24 and sdist/
wheel build 0.2.0 all passed after the fixes. Exact final commands/output are in
[verification evidence](TGPS-C01-verification.json). No second reviewer approval is claimed;
the executor verified the fixes by RED→GREEN and the full gates as the plan requires.
[Review disposition](TGPS-C01-review.md) records every finding and declined judgment.

Final code diff fingerprint from pre-C01 (same command as above): `8f6fc6c4e21277bd9a763a9e7af8a09f1701fecbf02fc1055638addb8ed3ee48`.
The earlier fingerprint identifies the before-review tree only. HEAD remains 80afe5a plus
uncommitted changes; no new commit/push/remote CI is implied. Task 1–5 are marked done;
milestone acceptance remains conditional because F09 is OPEN. Next session should review
this evidence/working tree and the open acceptance conditions, not reimplement the tasks.
