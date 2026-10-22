# C02B independent final code review

Date: 2026-10-22. Reviewer: `c02b_final_review`. Base:
`68fae3ab708b65ea7180b6de3cd03c9ae18f3c4d`; reviewed uncommitted working implementation.
Scope: approved C02B requirement0.1 / DEC-030 plan, scoped evidence README,
profile/readiness/calculation/material/pack1.2.0/catalog1.2.0,
discovery/candidate replay, HTTP adapter and browser transport/result/export.
Unrelated Stage4 draft excluded. This is code review, not acceptance or legal certification.

## Findings

1. **P2 — Summary calls an allowance subtotal all existing rights.**
   `examples/web/profile.js:64`: baseline-only profile breakdown iterates
   `tax_state.allowances` and labels its `total` “รวมสิทธิเดิม”, but RMF is a
   separate after-expense exemption and is absent from that subtotal and list.
   Reproduce with `calculate(rmf_request())` from
   `tests/acceptance/test_c02b_demo.py`: salary180000, expenses90000,
   allowances.total60000, RMFclaimed27000, taxable3000. Opening the existing-right
   summary therefore shows total60000 although applied existing rights total87000.
   The tax arithmetic is correct; the claimed explanation does not reconcile.
   Add the separately named RMF amount/combined total, or clearly name this
   subtotal as excluding RMF and refer to its separate breakdown. Preserve the
   domain distinction and avoid double subtraction.

2. **P2 — Material continuing conditions are visible only after acknowledgement.**
   `examples/web/index.html:29` acknowledgement select uses generic continuity /
   holding / redemption language; `examples/web/rmf.js:40` onward renders the
   pack-driven minimum5years, minimumage55 and maximum1yeargap only from a
   successful result. Reproduce: complete all positive RMF facts, leave
   acknowledgement unknown. Domain correctly closes the result, so the user
   cannot inspect those conditions before deciding to acknowledge them. The
   scoped contract calls for acknowledgement of displayed future obligations.
   Display reviewed pack-driven obligations alongside the acknowledgement,
   before READY, without assuming future compliance or hardcoding legal
   numbers in JS. Continue displaying the conditions in successful results/export.

3. **P3 — Coverage hint still describes RMF as blanket unsupported.**
   `examples/web/index.html:42`: hint above result says PVD is supported and
   “RMF / สิทธิอื่นและประวัติที่อยู่นอกขอบเขตยังปิดผลพร้อมระบุรายการ”. In the same
   view an ordinary first-purchase RMF produces a READY conditional estimate.
   Clarify the bounded first-purchase RMF route and distinguish combined/history
   cases that remain unsupported. This is misleading coverage copy, not a tax error.

## Checks and limitations

- Independent `uv run --locked pytest -q`: **810 passed in11.69s**.
- Independent `uv run --locked python -m examples.check_web_demo`:
  **48 passed,0 failed,0 skipped**, fresh server,4966.4744ms.
- Initial pytest attempt could not access default uv cache in sandbox; rerun
  with explicit escalation succeeded. A one-line reproduction initially failed
  due to PowerShell quote removal (`NameError`); corrected reproduction succeeded.
- Reviewed explicit presence/unknown, date chronology and confirmation identity /
  year / paid / date binding; prospective obligation material/hash; dated discovery
  replay and baseline-only early return; tax-impact guard; candidate replay;
  private error metadata and generic browser invalidation/version checks. No
  additional confirmed core arithmetic/readiness/replay or new-cash bypass finding.
- No new legal interpretation, legal certification, independent fresh amendment
  search or web research. Evidence applicability remains scoped as documented.
- Did not independently perform responsive screenshots, keyboard/reduced-motion
  runtime checks, all seven quality gates, fresh coverage measurement or delivery
  SHA/CI verification. Author was completing those checks; their absence here is
  not a finding or inferred failure. No published pack/catalog file is in tracked
  diff; new1.2.0 files are reviewed, historical byte pins remain author verification.
- Requirement/plan/roadmap progress headings were still being updated during this
  review; no stale-progress finding is raised against this in-progress checkpoint.

Review completed with three presentation findings above, pending author disposition
and the authorized single fix pass. No milestone promoted to ACCEPTED.
