# PVD follow-up — 2026-10-21

Status: **PARTIAL / legal gate OPEN**. No treatment or coverage change.

## Sources and custody

[manifest.json](manifest.json) records two downloaded originals and one failed
download. Their hashes refer to original response bytes, not extracted text.

| Source | Locator read | Dates and limitation |
| --- | --- | --- |
| [SEC PVD Act consolidation](https://www.sec.or.th/TH/Documents/ActandRoyalEnactment/Act/act-pvd2530-codified.pdf) | PDF1–4 / printed184–187, §§3,5,6,9,10 | Original Act signed1987-11-30, Gazette1987-12-07, effective1987-12-08 per PDF1 footnote. Consolidation contains amendment annotations through Act4; complete currency not certified. Read web-extracted text; direct download HTTP403, no local original/hash |
| [MR183](https://www.rd.go.th/2490.html) | §2 definitions, §§3–5,10 | RD consolidated HTML; corporate accounting periods from1989-01-01 under §10. Original publication date not established |
| [PND91 form in tax2025 directory](https://www.rd.go.th/fileadmin/tax_pdf/pit/2568/241268PIT91.pdf) | PDF2 ก1–7 / ข1,6; PDF3 deduction8 | PDF2 rendered and visually read; all3 pages text extracted. Year field is blank; directory provenance and matching tax2025 instructions do not establish tax2026 applicability |

## Findings and their limits

- Act §3 distinguishes statutory wages from generic employment income; overtime,
  holiday work pay and specified work-purpose payments are excluded. Do not infer
  wage basis from total salary, or classify every bonus identically by its name.
- §§5–6 distinguish employee savings from employer contributions and registration.
  §10 permits a minister-approved exception to the ordinary contribution range.
  A universal clipping formula for exceptional payments is therefore unverified.
- MR183 §2 adopts the Act's definitions in that regulation. Its corporate expense
  provisions do not independently establish an employee's PIT entitlement.
- Form PDF2 subtracts exemptions before expense, then deductions; ข1 identifies
  PVD above10,000. PDF3 deduction8 identifies the portion up to10,000.
  This directly corroborates the existing ordering inference for that form.

These observations do **not** establish annual aggregation across an individual's
employers. The Act's pooled-fund definition describes fund structure. It is not
an employee tax-aggregation rule. No directly applicable aggregation ruling was
located in this pass; search absence is not proof that none exists.

## Fixture disposition / next evidence

The existing nine draft fixtures remain unchanged and provisional. Their PVD
payments are within the ordinary15% wage range; the arithmetic receipt cannot
certify the generic scratch formula for payments outside that range. In particular,
do not turn its `min(paid, .15*wages, 500000)` into an approved engine rule.

LOW-WAGE remains an ordering diagnostic (taxable11500 versus incorrect3000,
both PIT0). Follow-up requirements before legal golden approval:

1. Establish annual/per-employer wage and contribution aggregation, including
   job changes, pooled funds and transfers; do not create numeric expectations
   from an assumed aggregation method.
2. Resolve exceptional authorized contribution rates against Code47(1)(ช) and
   MR126 §2(35), separating lawful fund payments from tax-exempt amounts.
3. Complete amendment currency and independent applicability/fixture review.

No new C02 RED/GREEN tests or implementation plan are claimed.
