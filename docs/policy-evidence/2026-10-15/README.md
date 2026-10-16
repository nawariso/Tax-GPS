# C01 — Evidence verification record

Verified on 2026-10-15. This record corrects provenance for existing numerical rules;
it does not certify all Thai tax law or activate artwork/solar.

## Social Security wage basis

- Primary: [Royal Gazette PDF 98728](https://ratchakitcha.soc.go.th/documents/98728.pdf).
- Ministerial Regulation for Section 33 wage bases, B.E. 2568; signed 11 December 2025,
  published 12 December 2025. Gazette volume 142, part 81 A, printed pages 5–6.
- Visually verified both rendered pages. Clause 1 establishes the effective date;
  clause 3(1), printed page 5, establishes the 2026–2028 wage floor/ceiling.
- Checked 2026 values remain 1,650 / 17,500 THB per month. No numerical policy change.
- Saved original: `sso-wage-base-2568.pdf`.
- Original-byte SHA-256: `529c7de6cbf8697e4777e1489639b60833131abece6f9bb7e7778c6ad3f6b07b`.
- The wage decree does not itself set the contribution rate. Existing supplemental
  government evidence for the 5% rate remains separately cited; not every temporary
  contribution exception was re-reviewed. Tax deduction uses actual paid contributions.

An initial government-mirror download contained an access-error page inside a PDF.
It was rejected and replaced by the verified direct Gazette document. Extension,
HTTP success and a checksum alone do not verify document content.

## Thai ESG / ESGX 2026 pool

- Primary: [SEC Q&A on LTF switching / Thai ESGX, set 1](https://www.sec.or.th/TH/Documents/Thai%20ESGX/QA-LTF-to-Thai%20ESGX-010468.pdf).
- Revision/footer date: 1 April 2025. Original posting timestamp was not established;
  current `published_at` is null rather than an invented date.
- Verified via web PDF text retrieval: page 1 treatment table and page 2 question 4
  support the 2026 cap/rate, holding period and shared pool for new purchases.
  Existing constants are corroborated, not increased.
- Local raw PDF download was blocked. No original SEC PDF bytes/checksum are claimed.
  URL/page references and this method/limitation are retained; the catalog hash
  identifies bundled data, not the remote PDF's bytes.
- LTF-switch rights are separate from new-cash purchases. C01 implements neither
  those carried deductions nor any deduction of capacity usage from baseline income.

The prior URL is a July 2025 investment-total news item; the recorded November date
and title did not match and it did not directly support the 2026 shared-pool claim.
Historical 1.0.0 keeps those values; current 1.0.1 uses matching evidence.

## Artifact selection

Current pack/catalog: 1.0.1. Historical 1.0.0 resources are unchanged. Loaders accept
supported `version` and optional `expected_hash`; reject unknown versions, traversal
and mismatched hashes. Current core 0.2.0 cannot impersonate core 0.1.1 for replay.
Historical catalog loading does not grant current candidate allocation authority.

This implementation verification record is not independent milestone acceptance.

## C01 completion recheck

On 2026-10-15 the direct Gazette PDF and SEC Q&A PDF text were retrieved again during
Task 3 verification. The same page/clause references above corroborate the bundled
scope; released 1.0.0 and 1.0.1 JSON were not edited in this continuation. The SEC
raw-file download/hash limitation remains. Historical byte comparisons and matching
old-engine replay are recorded in `docs/implementation-reports/TGPS-C01.md`.
