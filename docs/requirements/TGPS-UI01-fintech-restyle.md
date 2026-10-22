# TGPS-UI01 — Fintech visual restyle

Version: `0.1`
Date: `2026-10-15` (Asia/Bangkok)
Direction: **AGREED_DIRECTION** — user requested a look approximately like the reference.
Detailed requirement: **REVIEWED_FOR_IMPLEMENTATION** — user “โอเครครับ ลุย!”
Implementation: **IMPLEMENTED** — automated/source verification complete; rendered visual acceptance pending

## Intent and reference

Restyle the existing Thai local calculator using the visual direction of
[Fintech SaaS Landing Page Template by Kedhareswer Naidu](https://21st.dev/@kedhareswer/templates/fintech-saas-landing-page-template).
The public preview image was downloaded and visually inspected on 2026-10-15.
Observed features: deep forest outer frame, warm cream surface, large centered type,
muted secondary text, solid green/white buttons, fine circuit-like background lines,
and a soft gold decorative object. The page description also mentions dashboard cards
and a satin feature panel; these are descriptive source text, not a verified view of
the full interactive template. Browser automation had no available browser providers.
This requirement does not claim access to template source or a reusable code license.

## Proposed screen — authoring choices for review

1. Use a warm cream page inside a dark forest frame. Keep the TAX GPS identity and a
   small local-demo/year label in a compact navigation bar.
2. Center a larger Thai headline: “เห็นภาษีชัดขึ้น / ก่อนตัดสินใจใช้เงิน”, with a muted
   green second line and a short explanation. Keep vertical spacing compact enough
   that the working calculator remains easy to reach.
3. Use two genuine in-page actions: “เริ่มคำนวณภาษี” to the input section and
   “ลองสถานการณ์ตัวอย่าง” to the existing scenario selector. No empty menu/buttons.
4. Add subtle circuit-like lines and soft cream/green/gold accents using local CSS or
   code-native SVG decoration. Decorative elements must not resemble calculated tax,
   promised returns or an unimplemented account/product feature.
5. Retain the existing desktop input/result workspace below the hero, restyled as
   clean dashboard panels: lighter borders, restrained shadow, clearer number scale,
   dark forest primary tax card and calmer comparison cards. No ranked or recommended
   candidate styling. Keep all detailed inputs, scope copy and audit/export controls.
6. Stack input/results on mobile, reduce the frame/headline spacing, and confine wide
   comparison-table scrolling to its existing scroll region.

These layout/button/decoration details were proposed by the author and approved by the
user's subsequent “โอเครครับ ลุย!” on 2026-10-15.
The task is a restyle of the current calculator, not a replacement marketing-only page.

## Implementation boundary

- Scope: `examples/web/index.html`, `style.css`, `profile.css`; change presentation JS
  only if required for the two in-page navigation actions. Preserve existing element
  IDs and form names consumed by app/profile scripts and lifecycle tests.
- Keep the current standard-library server, static allowlist and local-only resources.
  Do not introduce React/Tailwind, external fonts/CDNs, analytics, storage or services.
- Do not copy the reference's brand, customer counts, testimonials, login/signup,
  subscription/trial, sync or accounting claims. Use only implemented Tax GPS actions.
- Tax core, packs/catalogs, readiness, eligibility, financial constraints, candidate
  generation and output/export semantics remain governed by C01 and existing contracts.
- No UI may expose stale results or financial output while the domain is not READY.
- This visual work does not advance C02–C06 or independent acceptance of C01/P1-004.

## Acceptance cases

| ID | Case | Expected |
| --- | --- | --- |
| UI01-AC01 | Desktop initial view | Cream/forest frame, centered Thai hero and restrained circuit accents recognizably follow the reference direction; TAX GPS identity remains |
| UI01-AC02 | Main actions | Both navigate to real existing input/scenario controls and are keyboard accessible; no dead links |
| UI01-AC03 | Supported default profile | Existing authoritative values remain PIT 79000, saving 18500 for a 100000 allocation; no illustrative numbers replace engine values |
| UI01-AC04 | Unknown/positive prior usage, retirement, malformed input | Existing C01 blocking/error identity and old-result/export invalidation behavior is preserved |
| UI01-AC05 | Desktop and mobile | Inspect 1440px and 390/360px layouts: no page-level overflow, clipped Thai copy, obstructed controls or unreadable money; table scroll stays internal |
| UI01-AC06 | Keyboard/reduced motion | Visible focus, usable labels/disclosures/buttons; decorations ignore pointer input and respect reduced motion |
| UI01-AC07 | Privacy/runtime | Assets stay local; no new external requests, storage, tracking or runtime dependencies |
| UI01-AC08 | Tracking and verification | Plan/checkmarks, ledger and verification evidence identify what changed and how; full locked gates and fresh-server lifecycle checked before completion |

## Verification and handoff

Use baseline evidence only when the current tree is verified unchanged; otherwise run
the session-start baseline before edits. Extend behavioral tests only for new behavior
(e.g. genuine navigation), and label already-passing cases as characterization.
Visual styling is assessed by rendering/screenshot inspection, not tests asserting CSS
strings. Run `tgps-verify` and preserve any known C01 limitations separately.
If browser automation remains unavailable, record that visual gate as unverified rather
than claiming screenshots were reviewed. Prepare a fresh local demo for user testing.

## Current progress

- [x] Read repository rules/current C01 handoff and inspect existing CSS/HTML.
- [x] Read the reference page and visually inspect its downloaded preview image.
- [x] Write concrete visual proposal, scope boundary and acceptance cases.
- [x] User reviews this description before product-code edits (AGENTS.md §5).
- [x] Write implementation plan and perform restyle after review.
- [x] Verify automatic gates, mark completed work/methods and provide updated local demo.
  ↳ 695 Python tests / 100% coverage, frontend24, smoke9/9; fresh source review clean.
- [ ] **PARTIAL:** Rendered desktop/mobile/keyboard review completed 2026-10-20;
  reduced-motion mode and user visual acceptance remain pending. See
  [rendered review](../implementation-reports/TGPS-UI01-visual-review-2026-10-20.md).

## Change log

| Date | Version | Change | Status |
| --- | --- | --- | --- |
| 2026-10-15 | 0.1 | Initial proposal based on user reference; no product-code edits | REQUIREMENT_REVIEW |
| 2026-10-15 | 0.1 | User approved; implemented local HTML/CSS with native links, automatic/source review passed; visual gates remain UNVERIFIED | IMPLEMENTED, not ACCEPTED |
| 2026-10-20 | 0.1 | Chrome rendered1440/390/360 and keyboard review; fixed decorative-dot mobile overflow with rendered RED/GREEN, full gates passed; reduced-motion mode/user acceptance pending | IMPLEMENTED, not ACCEPTED |
