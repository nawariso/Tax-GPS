# UI01 rendered review — 2026-10-20

Requirement v0.1, UI01-AC01/02/05/06/08. Base HEAD `da8e5c9` plus the
one-line CSS fix described below. IMPLEMENTED; user acceptance remains pending.
This adds evidence after the earlier browser-unavailable reports; it does not
erase those historical limitations or accept C01/P1-004.

## Findings and correction

Chrome extension browser became available. Started a new standard-library demo
on OS-selected loopback port57955 (exec session25382), preserving other processes.
Inspected screenshots at1440×1000,390×844 and360×800 with synthetic sample inputs.
Compared desktop with the saved public reference preview: cream/forest frame,
centered hero, restrained circuits and gold compass follow the approximate direction.

UI01-AC05 initially FAILED: at390, root client375/scroll385; at360,
client345/scroll355. Narrow circuit spans positioned their6px pseudo-element
19px from the right, giving negative left offsets; the mirrored right circuit
then extended the document. Fixed only `.circuit span::after` in style.css:
`right: clamp(0px, calc(100% - 6px), 19px)` keeps the dot inside the span while
preserving19px when space permits. No page-wide overflow hiding was added.

The same browser geometry check after reload PASSED:390=375/375,
360=345/345,1440=1425/1425. The15px client/viewport difference is the vertical
scrollbar. RED/GREEN here is a one-off rendered browser check, not a new automated
CI regression test. No CSS-string test was added for this presentation correction.
The existing695 Python tests and24 lifecycle cases remain unchanged.

## Rendered and keyboard checks

| Case | Observed result |
| --- | --- |
| Desktop/mobile hero, controls, default money | No clipping or page-level horizontal overflow in inspected views |
| Large synthetic salary at360 | All digits remain visible via line wrapping; metric client117/scroll117; long amounts can break across digit groups |
| Skip link | Tab reveals link; Enter focuses salary; settled top51.7px with visible outline |
| Both hero CTAs | Enter focuses the actual salary/scenario controls and scrolls them into view |
| Additional-input disclosure | Enter opens the real inputs; labels and hints remain readable |
| Comparison table | Focus outline visible; ArrowRight changes internal scrollLeft0→40 while page scrollX stays0; content1316/client268 |
| Unknown prior Thai ESG/ESGX usage | Named Thai alert wraps at390/360; prior result/candidates/export disappear |
| Default supported result | PIT79,000.00 and saving18,500.00 remain engine output |
| Reduced motion | Current browser reports reduce=false; source reduce rule reviewed, rendered reduce-mode test NOT RUN |
| Local assets | Existing /style.css, /profile.css, /profile.js, /app.js only; no added external assets/services |

Screenshots and browser measurements: [evidence directory](ui01-visual-2026-10-20/),
including [desktop](ui01-visual-2026-10-20/desktop-1440.jpg),
[mobile360](ui01-visual-2026-10-20/mobile-360-hero.jpg),
[mobile390](ui01-visual-2026-10-20/mobile-390-hero.jpg), and
[measurements](ui01-visual-2026-10-20/browser-checks.json).
Temporary viewport override reset; preview tab retained with default sample restored.

## Verification and review

Applied tgps-verify in its required order. Windows CPython3.14.3 / Node24.3.0:
sync clean, ruff clean, format148files clean, strict mypy102files clean,
pytest695 passed in11.61s, coverage100% (2846 statements/798 branches, zero misses),
fresh-server frontend24/24 (0failed/skip), sdist/wheel0.2.0 build passed.
[Command evidence](ui01-visual-2026-10-20/quality-gates.json).
These are local results for this CSS change, not a new remote CI run.

Fresh read-only reviewer `ui01_visual_fix_review` found0Critical/Important/Minor
in the one-line CSS delta. The reviewer checked source and reasoning, did not
independently rerun browser/gates, and did not grant milestone acceptance.

Remaining: rendered reduced-motion-mode check and user visual acceptance.
C01 F09 remains OPEN/conditional; no new diagnosis or legal acceptance is claimed.
C02 remains REQUIREMENT_REVIEW / implementation NOT_STARTED. No commit/push/merge.
