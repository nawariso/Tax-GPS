# C02 primary-source evidence and arithmetic review

Reviewed: 2026-10-21. Requirement C02 v0.1 / DEC-019.
Overall gate: **OPEN — not authorization for treatment implementation**.
Source text confirmation, arithmetic checking and legal applicability are distinct.

## Source custody and reading method

Original response bytes are preserved next to this file. [manifest.json](manifest.json)
contains URL, retrieval date, content type, byte length and SHA256 for every source.
PDF magic / HTML structure were validated before saving. HTML is a dated RD
consolidation snapshot, not an original gazette publication. `dg401.pdf` is also
an RD consolidated copy containing amendment annotations; its filename does not
establish original-version identity. Never overwrite these bytes on a later fetch.

| Artifact / official URL | Locator actually read | Dates / applicability established |
| --- | --- | --- |
| [Revenue Code](https://www.rd.go.th/5937.html), rd-code-38-64.html | Sections 42ทวิ, 47(1)(ก), 47(1)(ช); amendment notes | expense/personal provisions annotated Act44/2560; PVD allowance provision annotated effective 1991-01-01; original publication dates not independently established |
| [MR126 consolidation](https://www.rd.go.th/2502.html), rd-mr126.html | §2(35),(43),(54),(55),(61),(90),(102),(105)–(108) | PVD wording applies income from 2008; RMF amendment note MR357 applies income from 2020; full amendment-chain approval remains open |
| [MR395](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/mr395.pdf) | PDF1–3, Gazette printed1–3, clauses1–4 | signed2024-11-21, published2024-12-03; clause4 applies income from2024-01-01 |
| [MR398](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/mr398.pdf) | PDF1–4, Gazette printed8–11, clauses1–4 | signed2025-03-24, published2025-03-28; purchase/transfer windows specified separately, not inferred from signature |
| [DG401](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg401.pdf) | PDF1–4, clauses2–11 and amendment annotations | signed2021-01-27; effective income2020 onward under clause12; original publication date not established here |
| [DG414](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg414.pdf) | PDF1–3, Gazette123–125; clauses1–4,6 | signed2021-12-30, published2022-03-03; income2022 / filing2023 onward |
| [DG458](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/dg458A.pdf) | PDF1–6, Gazette14–18 plus annex; clauses1–11 | signed2025-06-24, published2025-07-25; clause11 effective2023-11-21 |
| [RD brackets](https://www.rd.go.th/fileadmin/user_upload/borkor/tax121260.pdf), rd-brackets.pdf | PDF1, entire table and exemption footnote | table states effective tax2017 onward; visually checked |
| [Decree470](https://www.rd.go.th/33893.html), rd-decree470.html | §4 and Gazette footer | signed/published2008-03-28; net income2008 onward |
| [Statutory rates](https://www.rd.go.th/5938.html), rd-rates.html | individual table and Act44 note | tax2017 onward |
| [PND91 instructions](https://www.rd.go.th/fileadmin/tax_pdf/pit/2568/Ins91_241268.pdf), rd-ins91-2568.pdf | PDF/printed3, exempt-income section; visually read | explicitly tax2025 / filing2026, not tax2026 instructions |
| [Expense infographic](https://rd.go.th/fileadmin/user_upload/callcenter/Q_A___Easy_Tax/Taxdeduct69.pdf), rd-taxdeduct69.pdf | all4 pages rendered/read; page1 employment expense | no explicit year/publication found; filename69 is not effective-date proof; supplementary expense corroboration only |

Web-extracted MR395/MR398/DG458 text was garbled. Rendered all 13 pages with
isolated PyMuPDF and visually read each, including signatures and annex. Rendered
pages are temporary under tmp/c02-pages; originals/hashes are the durable evidence.
DG401/DG414 readable text was checked separately and extracted locally for audit.
PyMuPDF was used through uv --no-project --with; project dependencies/lock unchanged.
The guessed dg458.pdf URL failed; the RD index linked the actual dg458A.pdf.
Failed retrieval is not source verification. Search snippets and old RMF FAQ were
not used as current-law authority.

## Rule matrix

TEXT_CONFIRMED means the cited content was read; it does not close the open
cross-rule/input/coverage questions below. Every row is for research, not activation.

| ID / AC | Rule observation (paraphrased) | Primary locator | Disposition |
| --- | --- | --- | --- |
| PVD-1 / AC03 | Employee contribution allowance up to10,000 | Code47(1)(ช) | TEXT_CONFIRMED; qualifying-fund conditions need chain review |
| PVD-2 / AC04,07 | Exempt portion above10,000 limited by15% wages and490,000 | MR126 §2(35) | TEXT_CONFIRMED; wage definition/aggregation OPEN |
| PVD-3 / AC04 | Exemption precedes assessable salary expense; allowance follows expense | Code42(17),42ทวิ,47; MR126 §2(35); PND91 tax2025 PDF3 exempt-income section | Statutory-order inference corroborated by prior-year filing split; independent current applicability/fixture review OPEN |
| RMF-1 / AC02,05 | Purchase continuity, holding/redemption conditions and exceptions | DG401 PDF1–2 clauses2–4 | TEXT_CONFIRMED; future-condition facts model OPEN |
| RMF-2 / AC05,07 | 30% taxable assessable-income basis;500,000 ceiling and retirement interaction | DG401 PDF2 clause5; MR126 §2(55) | TEXT_CONFIRMED; exempt-income basis/shared authority semantics OPEN |
| RMF-3 / AC05 | Transfer-acquired units do not create a new purchase deduction | DG401 PDF2 clause6 | TEXT_CONFIRMED; transfer/recapture excluded by approved scope |
| RMF-4 / AC02,10 | 2022-onward purchase requires taxpayer declaration; manager reports electronically | DG414 PDF1–2 clauses1–2; PDF3 clause6 | TEXT_CONFIRMED; distinguish taxpayer declaration from future manager-report completion |
| ESG-1 / AC06,07 | 2024–2026 qualifying purchases:30%,300,000, five-year holding | MR395 PDF1 clause1, PDF2 clauses3–4; DG458 PDF1 §2(1) | TEXT_CONFIRMED; eligible purchase classification OPEN |
| ESG-2 / AC06 | Special purchase window and LTF-switch rights have distinct treatment | MR398 PDF1 clause1, PDF2–3 clause4; DG458 PDF2–3 | TEXT_CONFIRMED; no ESGX/LTF treatment activated |
| ESG-3 / AC02,10 | Declaration/reporting and after-expense deduction ordering | DG458 PDF4 §6, PDF5 §§9,11 | TEXT_CONFIRMED; facts/coverage details OPEN |
| POOL-1 / AC05,07 | Inventory must account for other retirement categories | MR126 §2(43),(54),(55),(61),(90),(102) | Partial: list traced; cross-category cap/election review OPEN |
| BASE-1 / AC12 | Expense and personal allowance used in draft arithmetic | Code42ทวิ,47(1)(ก) | TEXT_CONFIRMED; existing C01 supported baseline preserved |

## Independent numeric fixture draft

[Nine fixtures](c02-numeric-fixtures-draft.json) were hand-authored, then checked
with Decimal arithmetic in an isolated scratch script with no tax_gps imports or
pack reads. [Arithmetic receipt](arithmetic-check.json) records exact fixture hash
and nine passes. These are **provisional**, not accepted legal golden cases or
engine tests. All quantities are synthetic and all eligibility facts are conditional.

PIT arithmetic follows the [official RD bracket table, PDF1](https://www.rd.go.th/fileadmin/user_upload/borkor/tax121260.pdf),
cross-checked against [statutory rates](https://www.rd.go.th/5938.html) and
[Decree470 §4](https://www.rd.go.th/33893.html). Original bytes/hashes for all three
are retained in the manifest; bracket PDF visually verified. SSO amounts are
explicit assumed paid amounts, not newly derived limits.

| Case | Main amounts / check | Taxable / PIT (THB) |
| --- | --- | --- |
| PVD-LOW-WAGE | salary180000; employee27000; employer99999 excluded; exemption17000; expense81500; PVD allowance10000 | 11500 / 0 |
| PVD-NORMAL | salary990500; SSO10500; PVD100000 | 720000 / 60500 |
| RMF-NORMAL | same salary/SSO; RMF100000 only | 720000 / 60500 |
| ESG-NORMAL | same salary/SSO; ThaiESG100000 only | 720000 / 60500 |
| COMBINED | same salary/SSO; PVD/RMF/ESG100000 each | 520000 / 30500 |
| RMF-PERCENT-CAP | salary990500; SSO10500; RMF350000; conditional claim297150 | 522850 / 30927.50 |
| ESG-PERCENT-CAP | same salary/SSO; ESG350000; conditional claim297150 | 522850 / 30927.50 |
| RETIREMENT-CAP | salary4000000; SSO0; PVD500000; RMF100000; conditional RMF claim0 | 3340000 / 767000 |
| PVD-BELOW-SPLIT | salary180000; SSO0; PVD8000; exemption0/allowance8000 | 22000 / 0 |

LOW-WAGE distinguishes ordering: incorrectly deducting all27000 after expense
would yield taxable3000 rather than11500. Both PITs are zero; testing PIT alone
would miss the error. Percentage fixtures intentionally contain no exempt-income
interaction. Combined claims are below percentage caps, avoiding an unresolved
RMF basis assumption. At RETIREMENT-CAP, PVD alone exhausts the conditional ceiling;
this does not establish a general optimization/election order.

## Remaining gate blockers and required next evidence

| Gap | Evidence/decision needed before implementation |
| --- | --- |
| G1 PVD wages and employer aggregation | [Follow-up](pvd-follow-up/README.md) traces Act §§3,5,6,9,10 and MR183 §2. Wage definition/fund structure read; multiple-employer PIT aggregation, exceptional contribution rates and currency remain OPEN. Do not equate annual salary/bonus with PVD wages implicitly |
| G2 PVD ordering | [Downloaded PND91 form](pvd-follow-up/README.md), PDF2 ก1–7/ข1 and PDF3 deduction8, directly corroborates exemption→expense→deduction. Current applicability and independent LOW-WAGE approval remain OPEN; not tax2026 instructions |
| G3 RMF basis/eligibility | Resolve treatment of exempt PVD amounts in taxable assessable-income percentage basis; define past facts versus future holding commitments and declaration/reporting timing |
| G4 shared authority | Reconcile statutory references to contributions paid with requirement's accepted-claim authority; review all retirement inventory and oversubscribed/election cases without input-order optimization |
| G5 ESG classification/pool | [Cross-rule follow-up](joint-follow-up/README.md): common2026 pool corroborated by SEC Q4 plus MR398/DG458; extra2025 new-money pool not carried forward. Product/class facts, currency and independent approval remain OPEN; LTF carry-forward separate and unsupported |
| G6 currency/evidence closure | Rates/filing-order originals now retained; complete material amendment-chain search as of review date and obtain independent fixture/rule review |

Gaps cannot be closed by assuming zero/eligible, copying old FAQs, passing existing
tests or obtaining a user's approval of legal accuracy. If a supported subset is
proposed instead, revise requirement/DEC explicitly; no subset was silently selected.
No implementation plan or runtime/rule-pack changes are authorized by this record.

## PVD follow-up custody

The [separate follow-up manifest](pvd-follow-up/manifest.json) adds two preserved
originals (MR183 HTML and PND91 form PDF), bringing downloaded originals to14.
It also records the SEC403 failure with null hash. Web-readable SEC text is useful
research evidence, but is not represented as a preserved original. The initial
12-source manifest and nine-fixture bytes/receipt are unchanged.

## Cross-rule follow-up — 2026-10-22

[Joint review](joint-follow-up/README.md) adds MR266→MR357 amendment lineage,
ESGX2026 pool corroboration and a concrete unresolved RMF basis comparison.
Its five downloaded originals bring custody to19, including one unrelated MR401
screened out; SEC Q&A raw download403 is the second failed retrieval overall.
Four [diagnostic arithmetic cases](joint-follow-up/diagnostic-cases.json) are
distinct from the original nine provisional fixtures: two unresolved RMF
alternatives, a conditional ESG pool example and an incorrect-pool comparator.
No hypothesis was selected as a legal rule. Overall gate remains OPEN.
