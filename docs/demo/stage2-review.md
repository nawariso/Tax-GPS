# Stage 2 profile demo — review handoff

Status: local verification passed; ready for separate demo review, not independently accepted.
Branch: `feature/demo-stage2-profile`.
Base: Stage 1 checkpoint `d15d840c4ee3f1ae50321ffb948a9f5f2be75c9a`.

## Authorization and boundaries

Stage 2 was explicitly authorized as a separate demo while P1-004 independent review and
remote CI remain pending. This does not permit core acceptance, merge, release, tagging,
or production use. The Stage 1 [checkpoint record](checkpoint-review.md) is historical
and remains a separate handoff; its test counts describe that earlier artifact.

No changes to `src/tax_gps/`, bundled rule packs, catalogs, engine versions, or governed
milestone status. No tax/financial formula is duplicated in the adapter or browser.
No persistence, recommendations, refund estimates, providers, or filing is added.

## Delivered artifact

- `examples/demo_profile.py`: strict extended input schema maps explicit caller facts to
  existing core models; unknown eligibility and unsupported income/retirement fail closed.
- `examples/web_demo.py`: existing production activation path plus normalized submitted
  profile and authoritative tax-state breakdown in the returned/exported result.
- `examples/web/profile.js` and `profile.css`: add/remove family, debt and payment records;
  life-coverage inputs and separate allowances/reserve explanation.
- `examples/web/index.html` and `app.js`: seven examples, caller-asserted eligibility,
  unsupported-field explanations, stale-result invalidation, and actual engine results.
- `tests/acceptance/test_demo_profile.py`: adapter equivalence, financial guardrails,
  explicit unknowns, malformed types/fields, unsupported inputs and deterministic output.
- `tests/web/test_app.cjs`: real-engine response lifecycle and profile regressions.
- `pyproject.toml`: repository root on pytest's import path for the examples adapter.

See the exact [input contract](input-coverage.md) and [operating guide](local-web-demo.md).
The default example intentionally supplies eligibility and empty record sets; it is not
an inference about the person opening the page. Legacy API requests remain narrower.

## Verification evidence

Local run on the project's uv-selected Python 3.14.3:

- 650 Python tests passed; the 42 demo/profile tests are included in this total.
- 10 JavaScript tests passed, using responses from the real local engine, not synthetic
  API fixtures. The DOM harness is not a replacement for browser rendering verification.
- Core `tax_gps` statement and branch coverage remained 100%; this does not measure
  demo adapter or JavaScript coverage.
- Ruff lint/format, strict mypy and source/wheel builds passed.
- Actual browser exercised all seven scenarios, coverage edits, unknown eligibility,
  unsupported retirement, debt removal, and JSON export containing the submitted profile
  with a result hash matching the displayed result.
- Normal/family/debt records at viewport widths 1440, 390 and 360 had no page-level
  horizontal overflow. The saved desktop family screenshot was visually reviewed.

Reproduce from the repository root:

```console
uv sync --locked
uv run --locked pytest --cov=tax_gps --cov-branch --cov-report=term-missing
uv run --locked python -m examples.check_web_demo
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict
uv build
uv run python -m examples.web_demo --port 8765
```

Open `http://127.0.0.1:8765/`. Browser evidence and downloaded illustrative JSON are
Git-ignored under `examples/artifacts/`, not runtime fixtures. Exports contain submitted
financial/profile facts; do not publish personal-data exports as review evidence.

## Self-check and remaining gates

This is a same-author self-check, not independent approval. No delegated review is claimed.
The added input keys are checked exactly, DOM text uses `textContent`, static serving uses
an explicit allowlist, and requests retain the loopback Host/Origin and 4096-byte limits.
These safeguards are appropriate to this local demonstration, not a production privacy
or security acceptance.

Remote CI for this exact Stage 2 commit: UNVERIFIED. The current workflow runs on
`push: main` or pull requests targeting `main`; a feature-branch push alone does not
trigger it. Canonical CI uses Python 3.12; the local run above is not remote-CI evidence.

P1-004 independent acceptance remains pending. Keep this demo branch separate and do
not merge it or advance core/production status on the strength of these local results.
Current legal freshness, document-based eligibility, persistence/privacy, and production
filing remain outside the artifact and must be addressed in later authorized stages.
