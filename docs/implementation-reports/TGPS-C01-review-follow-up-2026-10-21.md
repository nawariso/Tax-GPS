# C01 acceptance handoff review — 2026-10-21

Executor review of existing evidence, not a new independent domain/legal review.
Code checkpoint: `805e2d9ec6b18414b529642c74027335cbd505ff`.

## Disposition

- C01 Task1–5 remain IMPLEMENTED; do not repeat implementation.
- Existing C01 review's two Important findings have regression coverage and recorded
  fixes. Current Python suite: 695 passed; fresh-server frontend: 37/37, no skips.
- The UI checkpoint changes only five presentation/frontend-test files. It adds no
  C01 tax treatment, readiness, policy/catalog or transport-handler change.
- The earlier blanket UNVERIFIED remote/runtime/rendered notes are historical:
  remote evidence exists for c4527c9, current local full gates and rendered/reduced
  checks are recorded separately. Remote evidence for c4527c9 does not cover this SHA.
- C01 remains NOT ACCEPTED / conditional. Passing regressions does not certify all
  law or close the historical WinError10053 report.

## F09 remains OPEN

The [diagnosis](TGPS-C01-http-diagnosis.md) demonstrated unread rejected request
bodies in the archived handler and bounded draining in the current handler.
Both controlled old/current runs returned 100/100 responses; neither reproduced
the historical exception. No new reproduction or cause evidence was produced here.

If the error recurs, capture runtime versions, synthetic reproduction steps,
request boundary (Host/Origin/framing/size), response/exception and server lifecycle
without real user amounts. Compare a fresh isolated server and the historical
artifact as described in the diagnosis. Update the issue disposition only from
that evidence; successful unrelated probes are insufficient.

## Remaining acceptance decisions

1. Independent review of C01 acceptance matrix and material source limitations
   in [implementation report](TGPS-C01.md), including SEC raw-file hash limitation.
2. Explicit recorded acceptance disposition with F09 left conditional if still open.
3. New CI results tied to the pushed checkpoint's exact SHA.

Preparing C02 requirements/evidence can continue; this does not grant C02 release
or authorize new treatment code before its requirement/evidence gates.
