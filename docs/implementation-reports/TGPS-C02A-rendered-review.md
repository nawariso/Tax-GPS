# C02A integrated rendered review

Date:2026-10-22, Windows Chrome; actual local HTTP demo, synthetic values only.
Implementation IN_PROGRESS — runtime implemented; remaining verification below.

- Width1440: document scrollWidth1425;390:375;360:345;320:305. No horizontal
  page overflow observed. Viewport override reset after testing.
- Baseline example salary990500/SSO10500/PVD100000/wage990500, normal facts:
  PIT60500, taxable720000; comparison disabled with named baseline-only note.
- Low-wage example180000/PVD27000: taxable11500, exemption17000, expense81500,
  allowance10000. Detail initially collapsed, opens on demand. Confirms the
  rendered breakdown, not merely a zero PIT.
- Missing wage: result/export hidden. Opened grouped Thai error list and used
  Enter on link; document.activeElement.id became pvd_wage_basis. Restoring
  input enabled authoritative recalculation. PVD0 restored comparison availability.
- Post-review fresh server: wage990501 with salary990500 produced wage-field
  aria-invalid=true and named grouped link; no amount in error. Remittance=false
  correctly described late/pause/defer/outside prototype coverage; restored true
  yielded PIT60500/taxable720000.
- First generic role-selector attempts for summary/link found no match; used
  observed DOM summary/href selectors successfully. No passed check is inferred
  from a failed locator attempt.
- Fresh reduced-motion emulation **not verified**. F12 did not expose an
  actionable DevTools surface via available browser controls, and read-only
  matchMedia remained false. Existing UI02 reduced-motion source/runtime evidence
  remains historical evidence only; no OS/browser preference changed here.

Screenshots: [desktop](../demo/c02a-integrated-desktop.jpg),
[mobile](../demo/c02a-integrated-mobile.jpg). These are the integrated engine demo,
not the earlier standalone prototype. Screenshots do not establish user acceptance
or a complete screen-reader audit. Current live preview uses a fresh loopback port
written to ignored tmp/c02a-live.json; no persisted user profile/storage was added.
