"""Strict JSON loading for versioned opportunity catalogs."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date
from importlib.resources import files
from typing import Any, Never, cast

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.opportunity.models import (
    EvidenceRequirement,
    LockupMetadata,
    OpportunityCatalog,
    OpportunityCategory,
    OpportunityDefinition,
    OpportunityRule,
    OpportunityType,
)
from tax_gps.policy.loader import PolicyValidationError
from tax_gps.policy.models import RuleSource, RuleStatus, SourceAuthority

BUNDLED_CATALOG_ID_2026 = "TH-OPPORTUNITY-2026-001"
_TOP_KEYS = {
    "schema_version",
    "catalog_id",
    "version",
    "description",
    "jurisdiction",
    "tax_year",
    "currency",
    "status",
    "sources",
    "rules",
    "opportunities",
}
_SOURCE_KEYS = {
    "source_id",
    "title",
    "publisher",
    "authority",
    "url",
    "published_at",
    "retrieved_at",
}
_RULE_KEYS = {
    "rule_id",
    "version",
    "tax_year",
    "effective_from",
    "effective_to",
    "status",
    "source_id",
    "verified_at",
    "parameters",
    "supplementary_source_ids",
    "review_notes",
}
_DEFINITION_KEYS = {
    "opportunity_id",
    "name",
    "category",
    "type",
    "requires_new_cash",
    "intrinsic_need_required",
    "advisor_required",
    "effective_from",
    "effective_to",
    "rule_ids",
    "source_ids",
    "standalone_limit",
    "shared_limit_group",
    "lockup_metadata",
    "evidence_requirements",
    "catalog_version",
}


def _reject_float(value: str) -> Never:
    raise PolicyValidationError(f"float is not allowed in catalog JSON: {value}")


def _reject_constant(value: str) -> Never:
    raise PolicyValidationError(f"invalid JSON constant: {value}")


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyValidationError(f"{field} must be an object")
    return value


def _exact_keys(data: dict[str, Any], keys: set[str], field: str) -> None:
    missing = keys - data.keys()
    unknown = data.keys() - keys
    if missing:
        raise PolicyValidationError(f"{field} missing key: {sorted(missing)[0]}")
    if unknown:
        raise PolicyValidationError(f"{field} unknown key: {sorted(unknown)[0]}")


def _string(value: object, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise PolicyValidationError(f"{field} must be a string")
    return value


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise PolicyValidationError(f"{field} must be a boolean")
    return value


def _date(value: object, field: str, *, nullable: bool = False) -> date | None:
    text = _string(value, field, nullable=nullable)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise PolicyValidationError(f"{field} must be an ISO date") from exc


def _strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyValidationError(f"{field} must be a list of strings")
    return tuple(value)


def _source(value: object) -> RuleSource:
    data = _object(value, "source")
    _exact_keys(data, _SOURCE_KEYS, "source")
    try:
        authority = SourceAuthority(cast(str, _string(data["authority"], "authority")))
    except ValueError as exc:
        raise PolicyValidationError("unknown authority") from exc
    return RuleSource(
        cast(str, _string(data["source_id"], "source_id")),
        cast(str, _string(data["title"], "title")),
        cast(str, _string(data["publisher"], "publisher")),
        authority,
        cast(str, _string(data["url"], "url")),
        _date(data["published_at"], "published_at", nullable=True),
        cast(date, _date(data["retrieved_at"], "retrieved_at")),
    )


def _status(value: object) -> RuleStatus:
    try:
        return RuleStatus(cast(str, _string(value, "status")))
    except ValueError as exc:
        raise PolicyValidationError("unknown status") from exc


def _rule(value: object) -> OpportunityRule:
    data = _object(value, "rule")
    _exact_keys(data, _RULE_KEYS, "rule")
    year = data["tax_year"]
    if isinstance(year, bool) or not isinstance(year, int):
        raise PolicyValidationError("tax_year must be an int")
    parameters = _object(data["parameters"], "parameters")
    start = cast(date, _date(data["effective_from"], "effective_from"))
    end = _date(data["effective_to"], "effective_to", nullable=True)
    if end is not None and end < start:
        raise PolicyValidationError("effective_to precedes effective_from")
    return OpportunityRule(
        cast(str, _string(data["rule_id"], "rule_id")),
        cast(str, _string(data["version"], "version")),
        TaxYear(year),
        start,
        end,
        _status(data["status"]),
        _string(data["source_id"], "source_id", nullable=True),
        _date(data["verified_at"], "verified_at", nullable=True),
        parameters,
        _strings(data["supplementary_source_ids"], "supplementary_source_ids"),
        _strings(data["review_notes"], "review_notes"),
    )


def _definition(value: object, catalog_version: str) -> OpportunityDefinition:
    data = _object(value, "opportunity")
    _exact_keys(data, _DEFINITION_KEYS, "opportunity")
    try:
        category = OpportunityCategory(cast(str, _string(data["category"], "category")))
    except ValueError as exc:
        raise PolicyValidationError("unknown category") from exc
    try:
        opportunity_type = OpportunityType(cast(str, _string(data["type"], "type")))
    except ValueError as exc:
        raise PolicyValidationError("unknown type") from exc
    start = cast(date, _date(data["effective_from"], "effective_from"))
    end = _date(data["effective_to"], "effective_to", nullable=True)
    if end is not None and end < start:
        raise PolicyValidationError("effective_to precedes effective_from")
    limit_text = _string(data["standalone_limit"], "standalone_limit", nullable=True)
    lockup_raw = data["lockup_metadata"]
    lockup = None
    if lockup_raw is not None:
        lockup_data = _object(lockup_raw, "lockup_metadata")
        _exact_keys(lockup_data, {"minimum_holding_years", "measurement"}, "lockup_metadata")
        years = lockup_data["minimum_holding_years"]
        if isinstance(years, bool) or not isinstance(years, int):
            raise PolicyValidationError("minimum_holding_years must be an int")
        lockup = LockupMetadata(
            years, cast(str, _string(lockup_data["measurement"], "measurement"))
        )
    evidence_raw = data["evidence_requirements"]
    if not isinstance(evidence_raw, list):
        raise PolicyValidationError("evidence_requirements must be a list")
    evidence: list[EvidenceRequirement] = []
    for item in evidence_raw:
        entry = _object(item, "evidence requirement")
        _exact_keys(entry, {"evidence_id", "description"}, "evidence requirement")
        evidence.append(
            EvidenceRequirement(
                cast(str, _string(entry["evidence_id"], "evidence_id")),
                cast(str, _string(entry["description"], "description")),
            )
        )
    declared_version = cast(str, _string(data["catalog_version"], "catalog_version"))
    if declared_version != catalog_version:
        raise PolicyValidationError("opportunity catalog_version mismatch")
    return OpportunityDefinition(
        cast(str, _string(data["opportunity_id"], "opportunity_id")),
        cast(str, _string(data["name"], "name")),
        category,
        opportunity_type,
        _bool(data["requires_new_cash"], "requires_new_cash"),
        _bool(data["intrinsic_need_required"], "intrinsic_need_required"),
        _bool(data["advisor_required"], "advisor_required"),
        start,
        end,
        _strings(data["rule_ids"], "rule_ids"),
        _strings(data["source_ids"], "source_ids"),
        Money.of(limit_text) if limit_text is not None else None,
        _string(data["shared_limit_group"], "shared_limit_group", nullable=True),
        lockup,
        tuple(evidence),
        declared_version,
    )


def _duplicates(values: Iterable[str], field: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise PolicyValidationError(f"duplicate {field}: {value}")
        seen.add(value)


def parse_catalog(text: str) -> OpportunityCatalog:
    try:
        raw = json.loads(text, parse_float=_reject_float, parse_constant=_reject_constant)
    except (json.JSONDecodeError, TypeError) as exc:
        raise PolicyValidationError(f"invalid JSON: {exc}") from exc
    data = _object(raw, "catalog")
    _exact_keys(data, _TOP_KEYS, "catalog")
    if data["schema_version"] != "1":
        raise PolicyValidationError("unsupported schema_version")
    year = data["tax_year"]
    if isinstance(year, bool) or not isinstance(year, int):
        raise PolicyValidationError("tax_year must be an int")
    source_values, rule_values, opportunity_values = (
        data["sources"],
        data["rules"],
        data["opportunities"],
    )
    if not isinstance(source_values, list):
        raise PolicyValidationError("sources must be a list")
    if not isinstance(rule_values, list):
        raise PolicyValidationError("rules must be a list")
    if not isinstance(opportunity_values, list):
        raise PolicyValidationError("opportunities must be a list")
    version = cast(str, _string(data["version"], "version"))
    sources = tuple(_source(item) for item in source_values)
    rules = tuple(_rule(item) for item in rule_values)
    definitions = tuple(_definition(item, version) for item in opportunity_values)
    _duplicates((item.source_id for item in sources), "source_id")
    _duplicates((item.rule_id for item in rules), "rule_id")
    _duplicates((item.opportunity_id for item in definitions), "opportunity_id")
    return OpportunityCatalog(
        "1",
        cast(str, _string(data["catalog_id"], "catalog_id")),
        version,
        cast(str, _string(data["description"], "description")),
        cast(str, _string(data["jurisdiction"], "jurisdiction")),
        TaxYear(year),
        cast(str, _string(data["currency"], "currency")),
        _status(data["status"]),
        sources,
        rules,
        definitions,
    )


def load_bundled_catalog(catalog_id: str = BUNDLED_CATALOG_ID_2026) -> OpportunityCatalog:
    if catalog_id != BUNDLED_CATALOG_ID_2026:
        raise PolicyValidationError(f"unknown bundled catalog: {catalog_id}")
    resource = files("tax_gps.opportunity.catalogs").joinpath(f"{catalog_id}.json")
    return parse_catalog(resource.read_text(encoding="utf-8"))
