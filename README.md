# Tax GPS — Deterministic Tax Core

Phase 1.0 implementation of `TGPS-P1-001`: a deterministic, auditable Thai individual
income tax calculation core for Gregorian tax year 2026 (B.E. 2569 is display metadata only).

The authoritative specification is
[`docs/requirements/TGPS-P1-001-deterministic-tax-core.md`](docs/requirements/TGPS-P1-001-deterministic-tax-core.md).
The implementation report is
[`docs/implementation-reports/TGPS-P1-001.md`](docs/implementation-reports/TGPS-P1-001.md).

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
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, UserProfile

pack = activate_rule_pack(load_bundled_rule_pack(BUNDLED_PACK_ID_2026))

profile = UserProfile(
    profile_id="example",
    version="1",
    tax_year=TaxYear(2026),
    income=IncomeProfile(section_40_1=Money.of(990_500)),
    benefits=ExistingTaxBenefits(social_security_paid=Money.of(10_500)),
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

## Architecture

| Module | Responsibility |
|---|---|
| `tax_gps.core` | `Money`, `Percentage`, `TaxYear`, exact decimal context, canonical JSON, SHA-256 |
| `tax_gps.policy` | `RulePack`, `TaxRule`, `TaxBracket`, `LimitGroup`, `RuleSource`, loading, readiness, activation |
| `tax_gps.profile` | `UserProfile`, `IncomeProfile`, `ExistingTaxBenefits`, explicit eligibility inputs |
| `tax_gps.calculation` | pure PIT/expense/SSO/allowance/capacity rules and immutable result models |
| `tax_gps.engine` | deterministic orchestration producing `TaxState` |
| `tax_gps.audit` | `AuditSnapshot`, profile hashing, replay verification |

Domain logic is pure and framework-free. The Policy Readiness and Deduction Capacity decisions
are isolated so they map cleanly to the corresponding DMN decisions; no workflow engine is used.

## Policy packs

Tax constants live only in versioned policy packs, never in calculation code. The bundled
production pack is `src/tax_gps/policy/packs/TH-PIT-2026-001.json`.

Every material activated rule carries `rule_id`, `version`, `tax_year`, `effective_from`,
`effective_to`, `status`, `source_id`, and `verified_at`. Rule status follows
`DRAFT → VERIFIED → EFFECTIVE → SUPERSEDED → EXPIRED`.

Activation fails when a pack is not `EFFECTIVE`, when a required rule is missing, unverified, or
outside the tax year, or when a material rule lacks a resolvable authoritative HTTPS source.
Sources must be Thai law/Royal Gazette, the Revenue Department, a responsible government
authority, or an official provider. Blogs, social media, SEO pages, and AI output are rejected.

## Verification

Local verification uses the same locked dependency resolution and quality gates as
`.github/workflows/ci.yml` (Python 3.12 in CI):

```console
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
uv run pytest --cov=tax_gps --cov-branch --cov-report=term-missing -q
uv run pytest -m mandatory -q     # specification section 12 acceptance tests
uv run pytest -m boundary -q      # PIT bracket boundaries
uv run pytest -m golden -q        # personas G01-G03 and fixtures
uv run pytest -m negative -q      # invalid input, unsupported income, inactive policy
uv run pytest -m replay -q        # deterministic hash and replay
uv build
```

Coverage is gated at 100% statements and branches.

Engine and package version `0.1.1` expands calculation provenance to include every applied
rule's primary source followed by supplementary sources in Rule Pack order, deduplicated at
first reference. Because sources are part of canonical material output, hashes differ from
`0.1.0`; new `0.1.1` calculations and replay remain deterministic. Historical snapshots require
the matching `0.1.0` engine artifact.
