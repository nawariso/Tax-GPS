# UI02 verification follow-up — 2026-10-21

Status: IMPLEMENTED / USER_VISUAL_ACCEPTANCE_PENDING. C01 F09 remains OPEN;
C02 remains REQUIREMENT_REVIEW / implementation NOT_STARTED.

## Reduced-motion runtime check (UI02-AC07)

Opened a fresh loopback server at `http://127.0.0.1:59650/` and used native
Chrome DevTools command menu: `Emulate CSS prefers-reduced-motion: reduce`.
The browser's Styles accessibility tree showed the active reduced-motion rule,
animation name none / duration 0s, transition none and scroll-behavior auto,
all with !important. This is browser runtime evidence, beyond source inspection.

Changed synthetic salary 990500 → 200000 through the rendered input. Observed
pending feedback with old result amounts absent, followed by updated status,
PIT 0.00 and taxable income 29,500.00. Restored salary 990500 and observed
PIT 79,000.00 / saving 18,500.00. Selected `Do not emulate CSS
prefers-reduced-motion`; the reduced rule disappeared from active Styles,
then closed DevTools. No operating-system preferences changed.

Raw scoped accessibility evidence: [JSON](TGPS-UI02-reduced-motion-2026-10-21.json).
No frame-by-frame timing measurement, screen-reader audit or user acceptance
is claimed. This closes the runtime reduced-mode gap recorded on 2026-10-20
for the current UI02 source; it does not accept the milestone.

## Quality gates on the same source (this conversation)

| Gate | Actual result |
| --- | --- |
| uv sync --locked | passed; 16 packages resolved/checked |
| ruff check | clean |
| ruff format --check | 153 files already formatted |
| mypy --strict | clean, 102 source files |
| pytest + branch coverage | 695 passed in 11.66s; 2846 statements / 798 branches, zero misses, 100% |
| fresh-server frontend | 37 passed, zero failed/cancelled/skipped |
| uv build | sdist + wheel 0.2.0 built |
| git diff --check | clean before documentation follow-up |

Runtime: Windows CPython 3.14.3 / Node 24.3.0. These are local results,
not Ubuntu/Node22 remote CI. Browser checks and this follow-up change no
product source. SHA256 of app.js, index.html, profile.js, style.css and
test_app.cjs matches the existing UI02-source-hashes.json record.

## Recovery and next step

The previous turn's Computer Use stopped because it could not establish the
browser URL. No further UI input was sent in that turn. On this authorized
retry, opening the explicit loopback URL allowed the browser URL to be read.
An initial stale window ID and unavailable click geometry were handled by
fresh window/screenshot observations; no failed attempt is counted as a pass.

Next: user visual review of the existing UI02 presentation; C01 acceptance/F09
review; C02 detailed requirement and legal evidence gates before treatment code.
No commit, push, merge, new legal treatment or acceptance change in this follow-up.
