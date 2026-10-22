# C02 cross-rule review — 2026-10-22 Asia/Bangkok

Status: **PARTIAL / no implementation authorization**.
Retrieval crossed local midnight: manifest UTC2026-10-21T17:02 is Bangkok2026-10-22.
Keep the parent evidence bundle path and original bytes unchanged.

## Added source custody

[manifest.json](manifest.json): five downloaded originals, one HTTP403 failure.
Across all three manifests:19 originals, two failed downloads. A retained document
may be historical or irrelevant; custody count is not a count of approved rules.

| Official source | Locator read / date | Use and limit |
| --- | --- | --- |
| [MR266](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/266.pdf) | All5 PDF pages / Gazette7–11; clauses1–4, signature PDF4. Signed2008-05-16, published2008-05-28; clause1 applies income from2008-01-01 | Original PVD wording and retained RMF shared-cap paragraph; old RMF percentage superseded by MR357 |
| [MR357](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/mr357.pdf) | All4 PDF pages / Gazette4–7; clauses2,4,5. Signed2020-02-28, published2020-03-10 | Clause2 replaces only first paragraph of MR126 §2(55); clause4 preserves pre2020 purchases; clause5 income from2020-01-01. Does not erase the retained shared-cap paragraph |
| [MR401](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/mr401A.pdf) | PDF1 / Gazette4, title and clause1; Gazette2025-11-19 | Tourism measure, not DG401/RMF. Excluded as authority for C02; remaining pages not visually reviewed |
| [SEC ESGX Q&A](https://www.sec.or.th/TH/Documents/Thai%20ESGX/QA-LTF-to-Thai%20ESGX-010468.pdf) | PDF1 table, PDF2 question4; dated2025-04-01 in document | Web text read; raw download403/hashnull. Regulatory explanation, not replacement for tax legislation |
| [RD historic RMF FAQ](https://www.rd.go.th/60059.html) | Heading tax2017; questions2,6,7 | Historical15%/DG171 wording: REJECTED as current-rate authority. Useful counterexample to a blanket inference about all exemptions |
| [RD Clear Cut](https://www.rd.go.th/62777.html) | PVD Q1; RMF Q1; SSF Q1 | Supplementary corroboration only; page mixes historic measures. No new2026 SSO or other limits adopted |

PDF originals were format-validated, extracted and rendered with isolated PyMuPDF.
All MR266/MR357 pages were visually read. MR401 page1 was sufficient to reject
the unrelated result. Existing MR398 PDF1–2 and DG458 PDF1–4 were visually
cross-checked; their bytes and original manifest were not replaced.

## Findings ready for rule review

### PVD / RMF retained amendment chain

MR266 clause1 introduced the PVD split wording now in MR126 §2(35).
MR357 clause2 changes only the first paragraph of §2(55), leaving the retirement
aggregation paragraph traceable to MR266 clause4 / PDF3. DG401 clause5 repeats
the current30% taxable-assessable-income basis and contribution interaction.
This strengthens source lineage; it does not resolve multi-employer aggregation
or exceptional PVD rates. Corporate multi-fund rulings were not substituted for
an individual's PIT rule.

### RMF percentage base: explicit unresolved interpretation

DG401 clause5 says taxable assessable income. It does not explicitly identify the
PVD-exemption interaction. RD tax2017 FAQ question2 uses income before the elderly
exemption in that particular case. That historical answer is not current-law proof
for PVD; equally, it prevents treating the opposite blanket assumption as proven.

The [diagnostics](diagnostic-cases.json) compare two hypotheses using synthetic
salary990500, PVD100000, SSO10500 and RMF300000. With the same PVD exemption90000,
expense100000, personal60000 and PVD allowance10000:

| Hypothesis, neither approved | RMF percentage base / claim | Taxable / PIT |
| --- | --- | --- |
| Before PVD exemption | 990500 / 297150 | 422850 / 19785 |
| After PVD exemption | 900500 / 270150 | 449850 / 22485 |

The2700 PIT difference makes this an implementation blocker. Neither result is
an expected legal answer or added engine fixture. Needed: directly applicable
current interpretation of DG401 clause5 for MR126 §2(35), not generic expense-order
evidence or another copy of the same percentage phrase.

### ESGX2026 pool: corroborated, class mapping still needs review

SEC question4 explicitly puts new ESGX purchases from2026 in the ordinary ThaiESG
pool. MR398 clause1 limits the special new-money window to2025; its clause4 creates
the separate LTF-switch entitlement. DG458 §2(1) paragraph2 and §3(2) specify the
ordinary2024–2026 combined purchase ceiling. DG458 §2(2)/§3(3) concern the special
window; §4 concerns LTF switches. Thus the additional2025 pool must not be carried
forward as an extra new-money allowance in2026.

This corroborates the common-pool conclusion; it does not certify a product/class
merely because its marketing name contains ESGX. Before supporting a purchase,
establish its legal class and qualifying acquisition record. LTF carry-forward
remains outside approved treatment coverage; do not silently add its tax effect.

The conditional pool diagnostic uses salary1200000 and qualifying2026 purchases
200000+150000: a single300000 claim yields taxable740000/PIT63500; incorrectly
claiming350000 yields taxable690000/PIT56000. This tests the consequence of the
pool rule, not eligibility or election/allocation between classes.

## Input/time and shared-authority review questions

| Issue | Evidence anchor / next review needed |
| --- | --- |
| RMF continuity | DG401 §§2–4: distinguish acquisition history and exemptions from future holding/redemption conditions. A new purchase is not proof of future compliance |
| Declaration versus future report | DG414 §1 and DG458 §6: taxpayer declaration is distinct from manager submission, normally Jan15 following year. Do not default a future report to already completed or failed |
| Tax deduction versus paid contributions | MR126 §2(55) retained paragraph / DG401 §5 refer to contributions paid. Requirement's accepted-claim authority must preserve the statutory usage basis; a caller-provided usage total is insufficient |
| Oversubscription | Need rule review of inventory, excluded amounts and any election. No automatic optimization or input-order allocation is approved |
| PVD aggregation / exceptional rate | No direct applicable resolution located; questions remain as in PVD follow-up |

These are review findings, not a revised readiness contract. Existing unknown,
unsupported and precedence behavior remains unchanged. No plan, production
treatment, golden-fixture approval, milestone acceptance or release is claimed.

## Remaining work made concrete

1. Resolve the PVD aggregation/rate questions and the RMF two-hypothesis case above.
2. Review facts/class mapping and statutory usage against C02-AC02/05/06/07/10.
3. Check later material amendments and obtain independent rule/numeric review.
4. Record approved treatment details in requirement/DEC, then create the AC-linked
   implementation plan. Do not repeatedly search a phrase already preserved and
   treat duplicate results as additional legal certainty.
