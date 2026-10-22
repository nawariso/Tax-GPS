# Local demo checkpoint — review handoff

Status: locally verified; independent acceptance and exact-SHA remote CI pending.
This is a separately authorized UI artifact, not closure of P1-004 or production approval.

## Artifact boundary

- Checkpoint branch: `feature/local-web-demo-checkpoint`.
- Core base: `49339a1b23ea070ced32a335e83052902173bacf` (P1-004 R2).
- Core branch remains `feature/tgps-p1-004-candidate-allocation-outcome`.
- No changes to `src/tax_gps/`, policy packs, catalogs, or canonical milestone acceptance.
- The demo depends on the unaccepted R2 base; do not merge it ahead of core acceptance.
- Preserve reviewed history. No release, tag, squash, rebase, or merge was performed.

The review delta comprises the `examples/` adapter and browser assets, demo tests,
frontend lifecycle tests, documentation, mypy scope, ignored local artifacts, and
frontend verification steps in CI. The roadmap under `.hermes/plans/` remains a proposal.

## Verified local evidence

- Locked dependency sync: passed.
- Ruff lint and format: passed.
- Strict mypy: passed (96 source files, including examples).
- Python tests: 633 passed; 25 are demo adapter/HTTP tests.
- Core coverage: 100% statements and branches, not adapter or JavaScript coverage.
- Frontend lifecycle tests: 5 passed using real HTTP responses from the existing engine.
- Source and wheel distributions: built successfully.
- Browser: four scenarios, edited budget, invalid-input recovery, rights view, audit hashes,
  and rapid scenario changes checked; no horizontal overflow at 390 and 360 pixels.
- Earlier browser export verification is recorded in the demo guide and ignored local evidence.

The lifecycle regression fixes stale response publication: older success/failure/finally
handlers cannot overwrite newer state. Editing inputs invalidates the displayed result
and its export payload until recalculation. Server timing is controlled in the tests;
financial outcomes are not invented fixtures.

HTTP boundary tests reject untrusted hosts/origins, unknown routes, empty/oversized
requests, invalid length, conflicting transfer framing, and non-object JSON. Early
header rejection is tested without sending a body: closing a Windows socket with unread
payload can reset the connection before the client observes the rejection response.
This does not claim production-grade HTTP server security or load handling.

## Reproduce

From the repository root, with Python/uv and Node.js 22+ for frontend verification:

```console
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run python -m examples.check_web_demo
uv build
```

The frontend helper starts an isolated loopback server on an ephemeral port and shuts
it down after testing. No running demo instance is required for that command.

Run the interactive demo with `uv run python -m examples.web_demo`, then open
`http://127.0.0.1:8765/`. See [the guide](local-web-demo.md) for scope and assumptions.

## Remaining acceptance gates

1. Open a separate draft demo PR targeting main, explicitly dependent on P1-004 PR #3.
   The inherited core commits are not newly approved by that demo PR; review the UI delta
   against the exact base above. Do not merge either artifact without its required review.
2. Verify the PR head and CI checks against the published checkpoint SHA. The workflow
   runs only for main pushes and PRs targeting main; a feature-branch push does not prove CI.
3. Obtain independent P1-004 R2 acceptance and separate demo review.
4. Confirm Stage 2 UI scope and its prerequisite status before expanding input coverage.

PR/API access is blocked in the agent-controlled browser: GitHub rejected the saved login.
No raw credentials were extracted to work around that failure. Git transport and GitHub
PR authentication are separate capabilities. Remote PR creation and CI remain UNVERIFIED;
read back the remote branch SHA after publishing and record it in the delivery report.

Local tests and the same-author self-check are not independent review. The screen remains
LOCAL DEMO with explicit unknowns and pending acceptance. Production deployment, legal
freshness, persistence, ranking, product advice, and filing remain outside this checkpoint.
