# C04A E1 — Thai ESG evidence recheck for tax year 2569

Checked on 2026-11-26 (Asia/Bangkok) for [C04A](../../requirements/TGPS-C04A-thai-esg-year-end-what-if.md) E1.
This record corroborates the existing catalog rule. It does not change any number, and
it does not edit `TH-OPPORTUNITY-2026-001@1.2.0.json` or any earlier artifact.

## Source

- Revenue Department, *ภ.ง.ด.94 วิธีกรอกแบบแสดงรายการภาษีเงินได้บุคคลธรรมดา ครึ่งปี ปีภาษี 2569*
  — [Ins94_160669.pdf](https://www.rd.go.th/fileadmin/tax_pdf/pit/2569/Ins94_160669.pdf), 17 pages.
- Publisher authority: Revenue Department (official instruction for tax year 2569). The file name
  suggests 16 June 2569 (`160669`), but the publication date is not stated in the extracted text,
  so the date is recorded as unknown (`null`).
- Retrieved 2026-11-26 with `curl`. Saved original: `rd-ins94-2569.pdf`, a real PDF of 17 pages.
  It is not an HTML error page.
- Original-byte SHA-256: `4de4d7e86d807bcde766c645935c111c269f52e6e5f71556ee16a78396de5b40`.
- Text extraction: `rd-ins94-2569.pdf.txt` (`pdftotext -raw -enc UTF-8`), SHA-256
  `4a58ef2f6faed48fd588aaef0c64fec6bf9498f48ba06004310f8e8c1a50e134`.

## What the source supports (printed page numbers)

| Claim | Location | Result |
| --- | --- | --- |
| Purchases from 1 Jan 2567 to 31 Dec 2569 are exempt up to 30% of assessable income and at most 300,000 THB for the tax year | p.11, item 16.1, second paragraph; repeated for several funds in item 16.3 | Matches the catalog `assessable_income_rate 0.30` and `cap 300000.00` |
| Units bought in that window must be held for at least 5 years from the purchase date | p.11, item 16.2, second paragraph (other periods: 8 years) | Matches `minimum_holding_years 5` |
| Thai ESG is not part of the 500,000 THB combined retirement limit | pp.7–9: the combined-limit clauses list annuity insurance, PVD, GPF, private-school fund, RMF and NSF. Item 16 (Thai ESG) has its own cap and does not refer to the 500,000 limit | Supports D1. This rests on the absence of Thai ESG from the combined list, not on an explicit exclusion sentence |
| The taxpayer must notify the asset management company of the intention to use the right; the company reports to RD by 15 January of the following year | p.11, item 16.7 | Condition not in catalog `@1.2.0` (see F2) |
| Breaking the conditions loses the right for the years already claimed, with surcharge | p.11, item 16.5 | Informational; C04A shows the holding condition from the catalog |
| An exemption from switching LTF to Thai ESGX: tax year 2568 up to 300,000; tax years 2569–2572 the part above 300,000 up to 500,000, in equal parts per year (กฎกระทรวงฉบับที่ 398 (พ.ศ. 2568), DG notice no. 458) | p.12, item 17 | Separate right that affects the 2569 baseline (see F1) |

Treatment note: RD describes Thai ESG as an income exemption (เงินได้ที่ได้รับยกเว้น). The
existing catalog and engine apply it once as `FULL_ALLOCATION_DEDUCTION` through `tax_impact`.
C04A keeps that existing treatment and adds no second path.

## Findings for review

- **F1 — LTF→Thai ESGX switch exemption in 2569.** Users who switched LTF units in 2568 get an
  extra exemption in tax years 2569–2572. The current baseline (C01/C03) neither asks about it nor
  models it, so for those users the baseline PIT can be too high and a what-if saving would be
  misleading. This is a coverage gap that existed before C04A. It is proposed as decision D5 in the
  C04A requirement. No readiness change is made without a DEC.
- **F2 — notify-the-AMC condition.** Item 16.7 is a real usage condition. Catalog `@1.2.0` only
  carries the evidence requirement `FUND-PURCHASE`. Showing the notification condition in the
  product needs a new catalog version, or it stays out of the UI in v0.1. It is not added silently.
- **F3 — new-cash Thai ESGX in 2569.** This document does not describe new-cash Thai ESGX purchases
  in 2569 sharing the Thai ESG pool. The catalog note relies on the SEC Q&A. C04A v0.1 (D2) requires
  a confirmed zero for prior Thai ESG/ESGX purchases this year, so v0.1 does not depend on this point.

## Limitations

- The SEC Q&A PDF already cited in the catalog was requested again. The server returned an HTML
  page (13,730 bytes), not a PDF, so no SEC bytes or checksum are claimed. The same limitation is
  recorded in `../2026-10-15/README.md`.
- The text was checked through PDF text extraction only. No rendered-page visual check was
  possible: this machine has no PDF renderer (`pdftoppm` is not installed). Thai text extraction
  dropped some spaces, but the numbers and dates quoted above appear intact in both the `-layout`
  and `-raw` outputs.
- The primary ministerial regulation text for the Thai ESG 300,000 tranche was not retrieved from
  the Royal Gazette. Web search results naming กฎกระทรวงฉบับที่ 126 are an RD index page and
  were not verified. The RD instruction for the same tax year is used as the official source of
  the rule content.
- Secondary web results (bank and news pages) agreed on 30% / 300,000 / 5 years and on Thai ESG
  sitting outside the 500,000 limit. They are not cited as evidence.

## Result

E1 is **corroborated for the C04A v0.1 scope** (rate, cap, purchase window, 5-year holding,
separation from the retirement limit), with findings F1–F3 open for review. The catalog stays
`@1.2.0` and nothing is re-versioned.
