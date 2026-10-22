# Tax GPS — Deterministic Tax Core, Discovery, Guardrails & Candidate Outcomes

Phases 1.0–1.3 implement `TGPS-P1-001` through `TGPS-P1-004`: a deterministic,
auditable Thai individual income-tax core, opportunity discovery, financial guardrails,
and feasible candidate outcomes for Gregorian tax year 2026 (B.E. 2569 is display metadata only).

The authoritative specification is
[`docs/requirements/TGPS-P1-001-deterministic-tax-core.md`](docs/requirements/TGPS-P1-001-deterministic-tax-core.md).
The implementation report is
[`docs/implementation-reports/TGPS-P1-001.md`](docs/implementation-reports/TGPS-P1-001.md).
The discovery implementation report is
[`docs/implementation-reports/TGPS-P1-002.md`](docs/implementation-reports/TGPS-P1-002.md).

The candidate-allocation requirement is
[`docs/requirements/TGPS-P1-004.md`](docs/requirements/TGPS-P1-004.md).
The candidate implementation report is
[`docs/implementation-reports/TGPS-P1-004.md`](docs/implementation-reports/TGPS-P1-004.md).

## Product roadmap and requirements

The agreed product direction is recorded in the [roadmap](docs/ROADMAP.md) and
[decision log](docs/DECISIONS.md). The current milestone is
[TGPS-C01: baseline integrity](docs/requirements/TGPS-C01-baseline-integrity.md).
Its implementation is complete (Tasks 1–5, including fresh-review fixes); acceptance
is conditional with F09 OPEN, not ACCEPTED. Final local checks: 694 Python tests, 100%
statement/branch coverage, frontend 24/24 and build 0.2.0. See the
[C01 report](docs/implementation-reports/TGPS-C01.md) and
[C01 plan](docs/superpowers/plans/2026-10-15-c01-baseline-integrity.md) for per-task status. These records distinguish agreed direction, implementation evidence,
and milestone acceptance.

## Product and domain review

The [15 October 2026 review](docs/reviews/2026-10-15-product-domain-review.md)
records baseline deduction gaps, source-evidence issues, local verification results,
and proposed requirements for annual tax estimates and investment comparisons.
Its proposals do not change the accepted milestone contracts or legal policy versions.
Reproduce the synthetic retirement, unknown-parent and prior-purchase cases with:

```console
uv run python -m docs.reviews.reproduce_tax_gaps
```

## Interactive local demo

The Thai browser demo is a separately authorized presentation adapter, not part of the
P1-004 domain scope or independent acceptance. It calls the existing activation,
tax, discovery, guardrail and candidate engines without changing or duplicating rules.

From the repository root:

```console
uv sync --locked
uv run python -m examples.web_demo
```

Open `http://127.0.0.1:8765/` in your browser. Stop with Ctrl+C. Use `--port 8766`
if the default port is busy. The screen includes editable input, seven example scenarios,
baseline versus feasible outcomes, a user-selected comparison table, rights/conditions,
and JSON download. Choose the checkbox below a cash candidate to compare it with the
pinned NO_ACTION row; this is neither ranking nor an investment instruction.

The employee example calculates PIT 79,000 THB before and 60,500 THB after a 100,000 THB
allocation: tax saving 18,500 THB, cash outflow 100,000 THB, remaining spendable surplus
250,000 THB. These are executed engine outcomes, not estimated screen placeholders.

Important boundaries:

- Employee Section 40(1), bundled tax year 2026; the default example explicitly asserts
  personal allowance eligibility. Extended profiles can declare a different known status.
- Stage 2 accepts explicit parents/children, mortgage interest, debts, committed payments,
  and known/unknown life coverage. Eligibility is a caller assertion, not legal verification.
- Positive or unknown other income and retirement contributions block the demo: the current
  core does not deduct retirement contributions from PIT taxable income. No incomplete tax
  result is published for these profiles. See [input coverage](docs/demo/input-coverage.md).
- C01 gates the baseline in the domain: positive retirement or prior Thai ESG/ESGX usage
  is UNSUPPORTED; unknown shared usage is REQUIRES_INPUT. Neither publishes PIT, savings,
  candidates or stale exports. Explicit known zero/complete empty usage preserves the
  supported salary path. Actual treatment of existing purchases is deferred to C02.
- No ranking, recommendation, product choice, return forecast, tax withholding reconciliation,
  filing, authentication or persistence. Downloaded JSON contains submitted financial facts.
- Loopback-only HTTP server and explicit asset allowlist; no repository-wide file server,
  external services, fonts, analytics, browser storage or submitted-data logging.
- Existing bundled legal policy is used as-is; this demo does not reverify current law.
  P1-004 independent acceptance remains pending. This is not production approval.

See [the demo guide](docs/demo/local-web-demo.md) for scope and test commands,
and the [Stage 1 checkpoint handoff](docs/demo/checkpoint-review.md) plus
[Stage 2 handoff](docs/demo/stage2-review.md) and
[Stage 3 handoff](docs/demo/stage3-review.md) for review boundaries and remaining gates.

## Candidate allocations (P1-004)

`tax_gps.candidate.engine.build_candidates(tax, discovery, financial, guardrails, policy)`
produces feasible, bounded allocation compositions and deterministic outcomes only. It does
not rank, select, or recommend a candidate. `NO_ACTION` is present for READY tax baselines, and tax savings
come from the existing progressive PIT core, not a marginal-rate approximation. The caller
must pass an `ActivatedAllocationPolicy` bound by `activate_allocation_policy(raw_policy,
profile, tax, discovery, catalog)`. Build the raw production policy with
`bundled_allocation_policy(profile, tax, discovery, catalog)`, using the accepted
`UserProfile` and activated opportunity catalog. Activation binds the profile hash to
discovery, replays P1-002 from accepted profile/tax/catalog/planning-date evidence, and
independently verifies governed capacity with P1-002's capacity function and the profile's
shared-usage facts. A self-consistent discovery hash is integrity metadata, not authority
for remaining capacity. Unknown shared usage cannot become new-cash allocation. Activation
also verifies the EFFECTIVE bundled catalog and policy ID/version/year, P1-002 tax-saving
semantics and rule/source provenance. Only `FULL_ALLOCATION_DEDUCTION` is supported;
non-1:1 allocation-to-deduction is deferred pending separately governed upstream
policy/catalog support. Arbitrary caller treatments, unknown groups, and self-attested
content hashes cannot grant production authority. The candidate maximum remains 1–256,
with no more than eight allocatable opportunities. Raw profile facts are not serialized
into candidate audit records; state and policy hashes, exact allocations, tax, and
financial outcomes are retained.

See `tests/acceptance/test_candidates.py::_inputs` for a fully exercised construction
of TaxState, DiscoveryResult, FinancialState, GuardrailResult, and production policy
activation. Run `uv run pytest tests/acceptance/test_candidates.py tests/acceptance/test_candidate_policy_binding.py tests/acceptance/test_candidate_capacity_authority.py -q` to verify the integration.
Synthetic multi-opportunity cases test construction mechanics only and are never
activated as production policy.

## Scope

This phase calculates tax facts. It does not recommend, optimize, rank, or select anything.

In scope:

- exact decimal THB value objects (`Money`, `Percentage`, `TaxYear`);
- a versioned, source-backed policy pack with a production activation gate;
- progressive PIT, Section 40(1) expense, personal allowance, Section 33 social security;
- existing-right discovery for parent, child, and mortgage interest;
- generic standalone and shared deduction capacity;
- explicit unsupported-income states instead of approximation;
- material calculation trace, rule/source provenance, and deterministic SHA-256 audit replay.
- existing-right-first discovery for supported personal, parent, child, social-security and
  mortgage rights; standalone retirement capacity math does not authorize baseline deduction;
- a versioned opportunity catalog for Thai ESG, artwork, and Solar Rooftop;
- explicit intent, missing-input, effective-period, policy-readiness, and shared-pool decisions;
- immutable discovery snapshots and deterministic replay.

Out of scope (see specification section 17): UI, authentication, persistence, AI/LLM,
recommendation, product selection, projections, filing, corporate tax, and full 40(2)–40(8).

No AI service, network call, clock read, randomness, or database participates in a calculation.

## Requirements

- Python 3.12+ (developed and verified on CPython 3.14)
- [uv](https://docs.astral.sh/uv/)

The runtime has **no third-party dependencies**; only the standard library is used.

## Setup

```console
uv sync --locked
```

## Usage

```python
from tax_gps.audit import create_audit_snapshot, replay
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import calculate_tax
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, load_bundled_rule_pack
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, OpportunityFacts, UserProfile

pack = activate_rule_pack(load_bundled_rule_pack(BUNDLED_PACK_ID_2026))

profile = UserProfile(
    profile_id="example",
    version="1",
    tax_year=TaxYear(2026),
    income=IncomeProfile(section_40_1=Money.of(990_500)),
    benefits=ExistingTaxBenefits(social_security_paid=Money.of(10_500)),
    opportunity_facts=OpportunityFacts(shared_limit_usage=()),  # confirmed no prior usage
)

state = calculate_tax(profile, pack)
state.taxable_income  # Money('820000.00 THB')
state.pit  # Money('79000.00 THB')
state.tax_impact(Money.of(100_000)).saving  # Money('18500.00 THB'), not 20,000

snapshot = create_audit_snapshot(profile, state, pack)
replay(snapshot, profile, pack)  # raises AuditReplayError on any mismatch
```

Tax saving is always authoritative as `PIT(before) - PIT(after)`; `deduction × marginal rate`
is never reported as a result.

### Opportunity discovery

Discovery always requires an explicit `DiscoveryContext`; material decisions never read the
system clock. Capacity is a legal tax-treatment ceiling, not an amount to spend or a
recommendation.

```python
from datetime import date

from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import discover_opportunities
from tax_gps.opportunity.activation import activate_catalog
from tax_gps.opportunity.loader import load_bundled_catalog

catalog = activate_catalog(load_bundled_catalog())
context = DiscoveryContext(TaxYear(2026), date(2026, 9, 16))
discovery = discover_opportunities(profile, state, pack, catalog, context)

discovery.existing_rights  # existing rights are grouped first
discovery.opportunities  # deterministic catalog order; no ranking
```

The bundled artwork and Solar Rooftop rules fail closed as `RULE_NOT_READY` because complete
material legal conditions were not verified from authoritative full text. Metadata remains
visible for explainability, and explicit absence of intrinsic intent still returns
`INELIGIBLE` with `NO_INTRINSIC_NEED`. Thai ESG 2026 is active with a 30% assessable-income
limit, THB 300,000 cap, five-year holding metadata, and one shared Thai ESG/Thai ESGX pool.

## Architecture

| Module | Responsibility |
|---|---|
| `tax_gps.core` | `Money`, `Percentage`, `TaxYear`, exact decimal context, canonical JSON, SHA-256 |
| `tax_gps.policy` | `RulePack`, `TaxRule`, `TaxBracket`, `LimitGroup`, `RuleSource`, loading, readiness, activation |
| `tax_gps.profile` | `UserProfile`, `IncomeProfile`, `ExistingTaxBenefits`, explicit eligibility inputs |
| `tax_gps.calculation` | pure PIT/expense/SSO/allowance/capacity rules and immutable result models |
| `tax_gps.engine` | deterministic orchestration producing `TaxState` |
| `tax_gps.audit` | `AuditSnapshot`, profile hashing, replay verification |
| `tax_gps.opportunity` | versioned catalog, strict loading, provenance, readiness, activation |
| `tax_gps.discovery` | separable intent/period/eligibility/capacity decisions, orchestration, audit replay |

Domain logic is pure and framework-free. The Policy Readiness and Deduction Capacity decisions
are isolated so they map cleanly to the corresponding DMN decisions; no workflow engine is used.

## Policy packs

Tax constants live only in versioned policy packs, never in calculation code. The bundled
production pack is `src/tax_gps/policy/packs/TH-PIT-2026-001@1.0.1.json`; the catalog
current version is also 1.0.1. Unsuffixed 1.0.0 resources remain historical and unchanged.
Load them explicitly with `version="1.0.0"` and optionally `expected_hash`; loading an old
catalog does not grant current allocation authority. See [C01 migration and replay](docs/implementation-reports/TGPS-C01.md).

Every material activated rule carries `rule_id`, `version`, `tax_year`, `effective_from`,
`effective_to`, `status`, `source_id`, and `verified_at`. Rule status follows
`DRAFT → VERIFIED → EFFECTIVE → SUPERSEDED → EXPIRED`.

Activation fails when a pack is not `EFFECTIVE`, when a required rule is missing, unverified, or
outside the tax year, or when a material rule lacks a resolvable authoritative HTTPS source.
Sources must be Thai law/Royal Gazette, the Revenue Department, a responsible government
authority, or an official provider. Blogs, social media, SEO pages, and AI output are rejected.

## Verification

Local verification uses the same locked dependency resolution and quality gates as
`.github/workflows/ci.yml`. CI explicitly selects and asserts Python 3.12 for uv while disabling
automatic interpreter downloads; the repository's `.python-version` remains the developer
default and does not control the CI environment.

```console
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run pytest -m mandatory -q     # mandatory acceptance tests
uv run pytest -m boundary -q      # PIT bracket boundaries
uv run pytest -m golden -q        # personas G01-G03 and fixtures
uv run pytest -m negative -q      # invalid input, unsupported income, inactive policy
uv run pytest -m replay -q        # deterministic hash and replay
uv run python -m examples.check_web_demo  # real-engine frontend lifecycle tests; Node.js 22+
uv build
```

Coverage is gated at 100% statements and branches.

Historical engine and package version `0.1.1` expands calculation provenance to include every applied
rule's primary source followed by supplementary sources in Rule Pack order, deduplicated at
first reference. Because sources are part of canonical material output, hashes differ from
`0.1.0`; new `0.1.1` calculations and replay remain deterministic. Historical snapshots require
the matching `0.1.0` engine artifact.


Current C01 package/core is 0.2.0; discovery/candidates are 0.3.0. Incomplete baselines
carry machine reasons/missing IDs instead of usable PIT/savings/candidates. Parser errors
identify code-owned scalar paths or record indices; arbitrary parent identity is never
reflected in error metadata. This changes output hashes intentionally. Historical replay
must use the retained pre-C01 engine artifact described in the C01 report.


The approved [UI01 restyle](docs/implementation-reports/TGPS-UI01.md) gives the local
demo a cream/forest frame, centered Thai hero, native links into the real calculator,
and matching dashboard panels using only local HTML/CSS/SVG. Existing calculation JS
and domain rules are unchanged. Automatic/source verification passed (695 Python tests,
100% core coverage, frontend24); rendered desktop/mobile acceptance remains pending.

Handoff checks also passed in isolated local Windows Python3.12.14: 695 tests,
100% core coverage, frontend24 and all quality gates. Ubuntu/Node22 remote CI has
not run. See [verification](docs/implementation-reports/TGPS-handoff-verification.json).
The [C02 requirement](docs/requirements/TGPS-C02-existing-rights.md) is drafted for
review; no C02 treatment is implemented. Its [ledger](docs/implementation-reports/TGPS-C02-progress.md)
records the legal evidence and approval gates still pending.

Remote follow-up: [draft PR #4](https://github.com/nawariso/Tax-GPS/pull/4) now has
[successful CI run 10](https://github.com/nawariso/Tax-GPS/actions/runs/38765573860)
for head c4527c9 (merge ref b9015a3): Ubuntu24.04.5, Python3.12.15, Node22.23.3,
695 tests, 100% core coverage, frontend24/24 and all gates pass. See
[exact SHA/runtime evidence](docs/implementation-reports/TGPS-remote-ci.json).
This does not close F09 or rendered visual acceptance; the PR remains draft.

## UI02 — กรอกง่ายและคำนวณต่อเนื่อง

หน้า local demo แบ่งข้อมูลเป็น3หมวด พร้อมตัวอย่างและคำนวณอัตโนมัติหลังหยุดพิมพ์450ms. พื้นที่ผลลัพธ์คงอยู่ขณะตรวจข้อมูล; แสดงเฉพาะยอดล่าสุดจาก engine พร้อม motion เบา ๆ. รายละเอียด/ผลตรวจ/ข้อค้าง reduced-motion runtime และ user acceptance: [UI02 report](docs/implementation-reports/TGPS-UI02.md).

Follow-up 2026-10-21: reduced-motion runtime ตรวจแล้ว; ยังรอ user visual acceptance.
UI code checkpoint `805e2d9`, local Python695/coverage100%/frontend37 ผ่าน.
C01/F09 review และ [C02 scope review brief](docs/requirements/TGPS-C02-review-brief.md)
พร้อมอ่านต่อ; ยังไม่เริ่ม C02 treatment. ดู DEC-018 สำหรับ checkpoint/CI authorization

C02 follow-up2026-10-21: scope/behavior approvedตามDEC-019; อยู่ legal evidence
review, implementation NOT_STARTED. [Evidence matrix](docs/policy-evidence/2026-10-21/README.md)
มี12 original artifactsพร้อมhashและ9 provisional arithmetic fixtures; applicability
และ independent-review gapsยังOPEN จึงยังไม่เพิ่มtreatment

C02 follow-up2026-10-22: [cross-rule review](docs/policy-evidence/2026-10-21/joint-follow-up/README.md)
เพิ่ม amendment lineage และ ESGX2026 common-pool corroboration; custody19 originals
(รวมแหล่งที่คัดออก) และ4 diagnostic arithmetic casesแยกจาก9 fixturesเดิม.
PVD aggregation/exception, RMF basis และ legal-review gatesยังOPEN; implementation NOT_STARTED

UX draft2026-10-22: [C02 หน้าจอสิทธิเดิมที่อ่านง่าย](docs/requirements/TGPS-C02-guided-rights-ux.md)
เสนอแสดงภาพรวมก่อน แล้วเปิดสิทธิ/วิธีคิดตามต้องการ พร้อมบอกจุดที่ต้องแก้.
เป็นแบบสำหรับรีวิวตามDEC-020 ยังไม่ใช่หน้าจอที่ implementแล้ว

UX follow-up DEC-021: แบบได้รับอนุมัติแล้ว มี
[ต้นแบบลองกด](docs/demo/c02-guided-rights-preview.html) ให้ทดลอง3สถานการณ์จากข้อมูลสมมุติ.
เป็นdesign artifactแยกจากdemoจริง ไม่มีการคำนวณภาษีหรือstorage; C02legal gatesยังOPEN

C02A [scope](docs/requirements/TGPS-C02A-pvd-first-slice.md) ได้รับอนุมัติตามDEC-023:
เริ่มภาพรวมภาษีจากPVDกรณีพื้นฐานก่อน ไม่เปิดการทดลองเงินเพิ่มสำหรับpositivePVD
ในขั้นนี้. Bounded evidence เพียงพอสำหรับวางแผน; [แผน4tasks](docs/superpowers/plans/2026-10-22-c02a-normal-pvd.md)
รอรีวิว/เลือกวิธีทำงานก่อนลงcode. ไม่เปลี่ยนสถานะIMPLEMENTED/ACCEPTEDของparent

## C02A current checkpoint — 2026-10-22

Normal single-employer/single-fund PVD is integrated with the Thai demo. Core/package0.3.0, discovery/candidates0.4.0; positive PVD supports baseline/breakdown only. Explicit zero preserves supported planning when facts are complete. Local752 Python tests/100% core coverage/frontend45 and all seven gates pass. Remaining delivery checks and acceptance: [C02A progress](docs/implementation-reports/TGPS-C02A-progress.md). Earlier NOT_STARTED descriptions are historical; parent C02 legal gates and C01/F09 remain open.
