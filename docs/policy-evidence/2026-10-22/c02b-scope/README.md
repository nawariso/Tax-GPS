# C02B bounded first-purchase RMF evidence review

Date:2026-10-22, Asia/Bangkok. Scope approved DEC-028.
Disposition: **ADEQUATE_FOR_PLANNING_ONLY — not authorization for implementation**.
Purpose: determine whether this precise slice can be planned. No legal
certification, complete amendment-search claim or parent C02 gate closure.

## Source custody and bounded currency

[Manifest](manifest.json) preserves five new captures: MR126 consolidation,
ministerial index, income-DG index, DG401 andDG414. Four responses match previous
retained bytes; repeated downloads are not additional independent authorities.
Old originals/manifests and published packs/catalogs remain unchanged.

| Rule / issue | Primary locator and dates | Scoped interpretation to review |
| --- | --- | --- |
| RMF purchase percentage/type cap | [MR126 §2(55)](https://www.rd.go.th/2502.html); retained [MR357](../../2026-10-21/joint-follow-up/mr357.pdf) PDF1 §2, PDF3 §§4–5 |30%/500000 for income2020 onward. MR357 signed2020-02-28, Gazette2020-03-10. Earlier purchases explicitly retain old law; C02B excludes them |
| Qualifying ordinary own purchases | [DG401](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg401.pdf) PDF1 §2, PDF2 §§3,6 | Legal RMF/own current purchase distinct from PVD transfers/other acquisitions. Classification is an explicitly confirmed acquisition fact, never inferred from the fund name |
| History/ongoing conditions | DG401 PDF1 §2(1)–(4), PDF2 §§3–4 | First-ever current-year purchase avoids prior continuity/exception adjudication. Future continuity/holding/redemption obligations must be displayed; none is marked already fulfilled |
| Basis and ordering | DG401 PDF2 §5, PDF4 §11 |30% of taxable assessable income, typecap500000; exemption applied after statutory expenses. With explicit PVD0/no other exempt income, salary is the percentage base without choosing either combined-PVD hypothesis |
| Taxpayer declaration | [DG414](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg414.pdf) PDF1 §1 replacingDG401 §8(1) | Own purchases from2022 require declaration to the relevant AMC. DG414 signed2021-12-30, published2022-03-03, income2022/filing2023 onward (§6) |
| Manager reporting / correction | DG414 PDF2 §2 insertingDG401 §8/1 | Ordinary deadline Jan15 following year, unless otherwise determined; manager correction route exists. Pending before due date is not proof of completed reporting or statutory forfeiture |
| Existing salary expense/personal/PIT | [Code §§42ทวิ,47(1)(ก)](https://www.rd.go.th/5937.html), [RD rate table](https://www.rd.go.th/fileadmin/user_upload/borkor/tax121260.pdf), parent retained originals | Existing reviewed baseline constants retained; SSO figures below are assumed actual paid, not new legal maxima |

Current RD MR126 consolidation still annotates §2(55) toMR357. The ministerial
index (updated2026-10-12) lists403 downward; newer titles after357 inspected for
RMF-relevant amendments. Income-DG index inspected471 through401, including414
explicitly amending401. Later listed titles concern other matters (including
ESG/pension-insurance); these are not imported into C02B. Consolidated401 includes
414 annotations. No later directly material amendment was identified in this
bounded chain/index pass; this is not proof none exists outside reviewed sources.
One guessed web URL39854 failed; a general-DG navigation reached27995, which is
not the income-DG index; neither was used as applicability evidence. Actual index
19956 was then located/read and retained.

## Proposed fact/time contract for planning review

This section makes engineering choices explicit; it is not yet an approved
readiness implementation. It narrows to the already approved slice only.

1. Require explicit RMF purchase presence (`other_rights.rmf`) from the existing
   inventory. False is an actual no-purchase answer, so existing explicit-zero
   C02A profiles need no new RMF-detail answers. None remains missing. True
   requires own paid amount and complete ordinary first-purchase facts. A
   positive paid amount with presencefalse, or presencetrue/paid0, is a private
   field-level contradiction; do not silently choose one input.
2. Positive RMF requires known actual own purchase payments, legal ordinary RMF
   classification confirmed from purchase evidence, one fund/AMC, first-ever
   purchase this tax year, no distributions/borrowing, and existing other-rights/
   history inventory explicit negative. First purchase date and assessment date
   are supplied facts within2026, firstdate≤assessmentdate; no runtime clock.
   The cumulative paid answer is explicitly confirmed to cover actual purchases
   through that assessment date, not future intended purchases.
3. Declaration must be confirmed completed. Unknown is missing; not completed is
   a named unsupported current route, not a lifetime tax-forfeiture judgment.
4. Manager status is an explicit enum: NOT_YET_DUE or CONFIRMED_SUBMITTED;
   None is unknown/missing, and DISCREPANCY_OR_CORRECTION is unsupported. Require
   an explicit no-known-reporting-problem answer. NOT_YET_DUE must be before the
   ordinary deadline derived from the reviewed pack; CONFIRMED_SUBMITTED records
   the user-confirmed reporting fact. No status is inferred from absence or
   declaration. Filing2027 and deadline exceptions are outside C02B's2026
   assessment coverage, so no overdue adjudication is added.
5. Require acknowledgement of displayed future continuity/holding/redemption
   obligations; acknowledgement is not proof of future compliance. Missing
   acknowledgement asks for input; refusal stays unsupported for this
   conditional-estimate route, without declaring the purchase legally ineligible.
6. A supported positive RMF baseline is labelled **ประมาณการภายใต้เงื่อนไข RMF ที่
   ต้องปฏิบัติต่อเนื่อง** in summary, detail and baseline export. Code-owned
   condition codes bind the exact future obligations and pending-reporting notice
   into the material tax state/hash. They never say future holding is complete.
7. Positive RMF baseline-only disables planning/capacity/candidates/tax_impact/
   savings on all consumers. Existing PVDpositive/RMFzero and bothzero paths
   remain covered; combinedpositive is named unsupported before any cap formula.

These choices require review before implementation. They do not decide the
unresolved combined-PVD base, historical RMF breaches or future filing disputes.

## Independent arithmetic reference

[13 hand-authored cases](rmf-reference.json) contain literal expected amounts.
[Standalone Decimal check](rmf-reference-check.json) passes13/13 without importing
tax_gps or reading a pack. Expected expense and claim values distinguish RMF from
the PVD exemption-before-expense split. LOW-WAGE-ORDER yields expense90000 and
taxable3000; incorrectly moving RMF before expenses yields different values.
Percentage/cap boundary cases use explicit no-other-rights assumptions; no shared
allocation/election is exercised. EXACT-DERIVED documents existing exact-derived
Money convention, not a filing-rounding rule. No new rounding behavior is proposed.

Fixture hash: `b505ff74ffc7d82839f360bbbd90feeebbc9b6f9d749397bf251191a213c9734`.
Independent reviewer `c02b_scoped_builder_review` recomputed all13 cases with
PowerShell Decimal, no tax_gps/pack imports:13/13 match, including each percentage
cap/claimed/excess/expense/personal/taxable/PIT. Review disposition:
ADEQUATE_FOR_PLANNING_ONLY, not legal certification or an approved READY contract.
Reviewer read retained sources/narrative without a new independent web search.

## Independent review disposition and executor rulings

- Dates: put user-supplied assessment/first-purchase dates in RMF facts and
  material output/profile hash, not only DiscoveryContext. Domain validates
  chronology/year and consumers must reject a different planning date.
- Explicit negative presence skips only irrelevant RMF details; all existing
  required inventory/history checks remain. No fabricated false/true facts.
- Ongoing obligations also include not taking distributions/other fund money
  and not borrowing/withdrawing, not only holding/age/continuity. Conditions are
  prospective obligations, never already-fulfilled claims.
- Enums/READY/missing/unsupported are product contracts; DG414 does not enact
  them. Proposed choices remain subject to requirement/plan approval.
- CONFIRMED_SUBMITTED must carry a confirmation snapshot: fund name, AMC name,
  tax year, cumulative own paid and confirmation date. Snapshot identity/year/
  amount must match current facts, and firstpurchase≤confirmation≤assessment.
  Editing purchase/fund/AMC facts clears browser confirmation fields; domain
  independently rejects mismatches. This does not verify an AMC's system.
- Classification remains a user-confirmed documentary fact for the bounded
  prototype; no name heuristic or automatic registry lookup. One fund/AMC is
  system coverage, not a statutory restriction.

These rulings make the packet sufficient to author a reviewable plan only.
Unknown history, actual declaration, reporting facts and present compliance must
remain explicit; approval of an estimate is not proof of future compliance.

## Before planning

- Independent rule/contract questions and numerical recomputation must be
  recorded; any material unanswered question keeps that part open.
- If scoped evidence is adequate, record ADEQUATE_FOR_PLANNING_ONLY and include
  the exact proposed contract in requirement/DEC/plan for user review.
- No product/runtime edits, version activation, READY relaxation, parent legal
  closure, acceptance or release is authorized by this packet alone.
