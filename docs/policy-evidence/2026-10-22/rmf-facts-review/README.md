# C02 RMF fact and timing review

Date: 2026-10-22 (Asia/Bangkok). Status: **REVIEW_PACKET / G3–G6 OPEN**.
This is source analysis and a review checklist, not an approved readiness contract,
legal certification, implementation plan or activated tax treatment.

## What this pass adds

Separate facts already observable from future obligations and manager reporting.
Do not make a first-year purchase wait five years before claiming a current-year
deduction; equally do not describe future compliance as an observed fact. That
sentence is a product-contract question for review, not a new rule in the engine.
The unresolved RMF/PVD percentage-base diagnostic remains unchanged.

## Source custody and locators

[Manifest](manifest.json) records three downloaded originals and one failed SEC
retrieval. Previous originals, manifests and numeric fixtures were not replaced.

| Source | Locator read | Use and limitation |
| --- | --- | --- |
| [DG401](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg401.pdf), retained in the parent bundle | PDF1 §2; PDF2 §§3–6; PDF3 §8/8-1; PDF4 §§9–12 | Acquisition/history, percentage/shared basis, transfers, timing/order. This is an annotated consolidation; check DG414 for the amended wording. Signed2021-01-27, §12 effective2020-01-01 onward; current amendment completeness remains open |
| [DG414](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg414.pdf), retained in the parent bundle | PDF1 §1; PDF2 §2 (inserted8/1); PDF3 §6 and Gazette footer | Declaration and manager submission are separate duties. Signed2021-12-30, published2022-03-03, income2022/filing2023 onward. PDF2/printed124 visually inspected this pass |
| [PND90 instructions tax2568](https://www.rd.go.th/fileadmin/tax_pdf/pit/2568/Ins90_241268.pdf), new original | PDF1 year label; PDF14 §§18.1–18.9 | Prior-year ThaiESG cross-check, not tax2569 instructions/certification. PDF14 visually inspected: annual income basis and the2024–2026 exception are printed; a search excerpt mentioning income only up to purchase date was not accepted as source text |
| [RD Clear Cut page titled tax2563](https://www.rd.go.th/62149.html), new original | RMF Q13 items1,3 | **REJECTED for current numeric/continuity authority**: still displays15% and an investment minimum despite the year in its title. Heading, crawl date and official hosting alone do not prove applicable law |
| [RD current-law index](https://www.rd.go.th/21221.html), new original | First displayed result page; top entry dated2026-10-14 | Bounded reconnaissance only. No relevant title on a single page does not establish a complete amendment search or closeG6 |
| [SEC tax-saving funds](https://insight-fund.sec.or.th/mutual-fund-info/tax-saving-fund) | Web-readable RMF/declaration summary | Direct download FAILED/HTTPError, hashnull. Generic corroboration only, no preserved original or applicability closure claimed |

## Fact/time review matrix

All field concepts below are proposals for a later reviewed requirement, not new
model fields or current readiness defaults. Unknown remains unknown.

| Issue | Evidence anchor | Required distinction / question before implementation |
| --- | --- | --- |
| Actual purchase versus holdings | DG401 §§2,6 | Current-year own purchase payments differ from opening holdings, transfers and PVD-to-RMF receipts; do not count a transfer as a purchase |
| Purchase qualification | DG401 §2 opening | Establish RMF legal classification and acquisition record, not a fund-name substring or marketing label |
| Past continuity | DG401 §2(1), transitional paragraph, §§3–4 | First-ever purchase, a prior purchase history and statutory exceptions are different cases. Absence of a history object cannot assert first-ever purchase |
| Multiple RMFs | DG401 §3 | Check every fund’s relevant conditions; a total amount or one fund’s valid facts cannot prove all funds eligible |
| Holding/redemption | DG401 §2(2), §4 | Past events can be confirmed; future holding/redemption conditions must be disclosed as obligations, never recorded as already satisfied. Review how a conditional estimate is labelled |
| Other fund benefits/borrowing | DG401 §2(3)–(4) | Distinguish distributions/withdrawals/borrowing from ordinary own purchases. Unknown cannot silently pass |
| Taxpayer declaration | DG414 §1 replacingDG401 §8(1) | Purchases from2022 require declaration to the relevant AMC. Do not substitute intended future declaration or manager reporting for the taxpayer’s completed act |
| Manager submission | DG414 §2 insertingDG401 §8/1 | Ordinary submission deadline is Jan15 next year, subject to a different director-general determination. A report not yet due is not automatically failed/completed. Review filing-time evidence/corrections separately |
| Late/corrected report | DG414 §8/1 second paragraph | A correction/late-information route exists. Do not invent automatic permanent tax forfeiture from a missing report flag |
| Percentage/shared authority | DG401 §5; MR126 §2(55) | Retain actual purchase/qualifying amount/claim separately. Combined-PVD base and contributions-paid versus accepted-claim shared usage remain unresolvedG3/G4 |
| Placement in tax calculation | DG401 §11 | Deduction after statutory expenses; this ordering does not itself resolve the separate percentage-base question |

## Concrete review cases (not legal golden fixtures)

1. First-ever2026 purchase, known own payment and classification, declaration
   completed, no disposal/borrowing/other retirement rights: identify present facts
   versus future obligations; no claim that future conduct has been verified.
2. Same purchase, declaration unknown: name the missing declaration, not manager
   submission; do not supply false or true.
3. Same facts before ordinary next-year submission deadline, manager report
   pending: do not infer either noncompliance or completed reporting.
4. After a filing-time discrepancy/correction: reviewed route needed; do not
   silently convert it into the ordinary purchase path.
5. Current payment0 but prior RMF history: zero does not answer continuity or
   recapture questions. Preserve named unsupported/missing behavior.
6. Transfer from PVD with no new purchase: acquired units do not become a current
   purchase deduction merely because they are held in an RMF.
7. One eligible fund plus another with unknown facts: all relevant facts must be
   assessed; no aggregation shortcut that drops unknown eligibility.
8. Positive PVD plus RMF: retain the two existing alternative diagnostics; neither
   becomes an expected legal result through this fact/time review.
9. Year/amount/percentage/shared boundaries: independent arithmetic and reviewed
   source applicability are both required before promoting expected tax outputs.

## Disposition and next step

- G3 fact/time questions are now separated into reviewable cases; they are not
  closed merely by writing this matrix. G3 combined-PVD basis remains unresolved.
- G4 shared-authority/election andG5 ESG class/current applicability remain open;
  G6 has only a bounded index inspection, not exhaustive negative evidence.
- A separate RMF-only staged scope could avoid the combined-PVD ambiguity, but
  would narrow READY coverage and therefore needs an explicit requirement/DEC
  review before implementation. It is a proposal, not inferred user approval.
- No new product code, legal number, artifact version, readiness behavior,
  planning availability or milestone acceptance changes in this pass.

Search disposition: targeted RD queries for direct RMF/PVD basis/current401/414
interpretation did not produce a directly resolving current ruling. SET training
examples and generic summaries were screened as corroboration, not substituted
for that missing authority. Prior contrary hypotheses/receipts are preserved.
