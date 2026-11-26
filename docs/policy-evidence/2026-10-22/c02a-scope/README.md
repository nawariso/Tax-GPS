# C02A bounded evidence review

Reviewed: 2026-10-22, Asia/Bangkok. Scope approved in DEC-023.
Disposition: **ADEQUATE FOR PLANNING ONLY** for normal employee contributions,
one employer/one fund, no other positive rights or relevant history. This is a
bounded engineering evidence review, not legal certification or product acceptance.
Parent C02 G1–G6 are not collectively closed by this record.

## Custody and currency

[manifest.json](manifest.json) preserves four fresh RD HTML responses with
retrieval timestamps, content types, lengths and SHA-256. Two SEC raw downloads
returned HTTP403: no original bytes/hash are claimed for those. SEC contents were
read using the web reader, as was the Act consolidation already recorded in the
[earlier follow-up](../../2026-10-21/pvd-follow-up/README.md).
Old originals and provisional fixtures remain byte-for-byte unchanged.

| Source | Locator read / finding | Dates and limitation |
| --- | --- | --- |
| [Code](https://www.rd.go.th/5937.html) | §§42(17),42ทวิ,47 opening and47(1)(ช): exemption framework, expense then allowance; actual employee contributions up to10000 and qualifying-fund cross-reference to65ตรี(2) | PVD allowance annotated effective1991-01-01; expense/personal annotated Act44/2560. Original allowance Gazette date not established here |
| [MR126](https://www.rd.go.th/2502.html) | §2(35): employee contribution,15% wages, excess over10000 up to490000; no sunset in this provision | Consolidation footer updated2026-01-13; clause income2008-01-01 onward. Read with [MR266](https://www.rd.go.th/fileadmin/user_upload/kormor/newlaw/266.pdf) PDF1§1, signed2008-05-16/published2008-05-28, preserved earlier |
| [MR183](https://www.rd.go.th/2490.html) | §2 fund/wages/employee refer to PVD Act; §§3–5 refer expressly to employer corporate expense and correction/approval; §§6–10 reviewed for scope | Consolidated text; publication unknown/null, §10 corporate accounting from1989-01-01. Does not establish an automatic employee PIT disallowance for every employer expense defect |
| [PVD Act](https://www.sec.or.th/TH/Documents/ActandRoyalEnactment/Act/act-pvd2530-codified.pdf) | PDF1§3 wages; PDF2§§5–6 registration/separate employee/employer money; PDF3§9 articles; PDF4§10 ordinary rates2–15%, three-working-day remittance and exception; §10/1 pause/defer authority | Signed1987-11-30/published1987-12-07/effectiveDec8, consolidation includes Act4/2558; consolidation publication date unknown, raw403 as earlier record |
| [RD ministerial index](https://www.rd.go.th/6160.html) | Read latest403/2569 through399/2568 entries and linked126/183 references. New403 early defence retirement,402 electronic tax,401 tourism,400 art and399 digital assets are different subject matter | Index inspected2026-10-22; not an exhaustive Gazette search or proof of no possible amendment |
| [SEC13162](https://www.sec.or.th/TH/Pages/News_Detail.aspx?SECID=13162) | News161/2569: five-year Act assessment consultation, comments throughOct2 | Published2026-08-03; consultation is not enacted amendment |
| [SEC13302](https://www.sec.or.th/TH/Pages/News_Detail.aspx?SECID=13302) | News184/2569: **published guidelines** for pooled-fund articles; pooled fund describes fund structure, not a taxpayer's multiple-employer aggregation rule | Published2026-09-07; guidelines are not a replacement PIT cap/rate. **CORRECTION:** an earlier working description called this a draft; actual text says published guidelines |

Bounded search also used RD-focused queries for contributions/remittance delays
and47(1)(ช)/183. Returned third-party results were excluded. This review found
adequate direct text for the declared normal slice; it does not assert that every
2026 law has been searched. Prior-year PND91 is corroboration for order only,
not authority that the2025 form is the2026 form. New applicable evidence requires
reopening review before activation.

## Qualifying-fund and facts contract

Trace: Code47(1)(ช) → ministerial qualifying conditions → MR183§2 →
PVD Act§§3,5–6,9–10. Registration alone is not the full contract.
Employee paid means money actually credited into the registered fund in the
tax year, identifiable from fund/employer statements; payroll withholding alone
does not establish that fact. Ask separately for registration, actual-credit
confirmation, wage basis for contribution periods, one employer/one fund and
ordinary article-rate confirmation. No preselected eligibility answers.

Known late/irregular remittance, authorized pauses/deferments, special rates,
disputed/uncredited amounts or multiple-employer/fund facts are outside this
slice; report a named coverage reason, not a claim that all such employees lose
their legal entitlement. Unknown required facts remain REQUIRES_INPUT.
Do not demand corporate expense approval, inspect employer accounts or ask the
user to certify that every legal provision is met. MR183§§3–5 expressly concern
corporate expense consequences; importing those as an automatic employee penalty
would be an unsupported inference. This slice claims only this taxpayer's own
employee contribution; it adds no spouse-derived allowance or blanket ban on
married taxpayers.

Calculation for confirmed normal coverage: allowance=min(paid,10000),
exemption=min(max(paid−10000,0),490000); expense on salary minus exemption;
allowance after expense. Employee and employer contribution limits are distinct;
employer money never increases employee allowance. Wage basis is explicit and
never silently set to gross salary. Percentage-base questions for RMF/new cash
remain excluded through the approved baseline-only positive-PVD contract.

## Independent review and numeric references

Read-only reviewer `c02a_evidence_review` independently recalculated the original
nine cases using PowerShell Decimal: **9/9**. Initial evidence verdict required
the currency and qualifying-fund chain above; follow-up verdict: **adequate for
planning only once recorded**, without requiring complete parent-law certification.
No engine imports or implementation were reviewed and no legal acceptance granted.

Original employer99999/low-wage case remains an arithmetic invariance diagnostic,
not a normal-fund legal golden. [New normal reference](normal-pvd-reference.json)
uses ordinary positive employer contributions, without changing employee expected
outputs. Its [receipt](normal-pvd-reference-check.json) checks both parties' normal
ratios plus split/order/taxable/PIT with independent Decimal arithmetic.
Reference status is for implementation planning, not engine-test pass or acceptance.
