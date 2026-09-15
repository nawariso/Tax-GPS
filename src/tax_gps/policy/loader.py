"""Strict JSON loader for immutable rule packs."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date
from enum import StrEnum
from importlib.resources import files
from typing import Any, Never, cast

from tax_gps.core.canonical import canonical_json, freeze, sha256_hex, thaw
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.models import RulePack, RuleSource, RuleStatus, SourceAuthority, TaxRule

BUNDLED_PACK_ID_2026 = "TH-PIT-2026-001"
_SCHEMA_VERSION = "1"
_TOP_KEYS = {
    "schema_version",
    "rule_pack_id",
    "version",
    "description",
    "jurisdiction",
    "tax_year",
    "currency",
    "status",
    "sources",
    "rules",
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


class PolicyValidationError(TaxCoreError, ValueError):
    """A serialized rule pack is malformed or structurally invalid."""


def _reject_constant(value: str) -> Never:
    raise PolicyValidationError(f"invalid JSON constant: {value}")


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyValidationError(f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    missing = expected - value.keys()
    unknown = value.keys() - expected
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


def _date(value: object, field: str, *, nullable: bool = False) -> date | None:
    text = _string(value, field, nullable=nullable)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise PolicyValidationError(f"{field} must be an ISO date") from exc


def _enum[T: StrEnum](enum_type: type[T], value: object, field: str) -> T:
    text = cast(str, _string(value, field))
    try:
        return enum_type(text)
    except ValueError as exc:
        raise PolicyValidationError(f"unknown {field}: {text}") from exc


def _string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PolicyValidationError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise PolicyValidationError(f"{field} must contain only strings")
    return tuple(value)


def _source(value: object) -> RuleSource:
    data = _object(value, "source")
    _exact_keys(data, _SOURCE_KEYS, "source")
    published_at = _date(data["published_at"], "published_at", nullable=True)
    retrieved_at = _date(data["retrieved_at"], "retrieved_at")
    retrieved_at = cast(date, retrieved_at)
    return RuleSource(
        source_id=_string(data["source_id"], "source_id") or "",
        title=_string(data["title"], "title") or "",
        publisher=_string(data["publisher"], "publisher") or "",
        authority=_enum(SourceAuthority, data["authority"], "authority"),
        url=_string(data["url"], "url") or "",
        published_at=published_at,
        retrieved_at=retrieved_at,
    )


def _rule(value: object) -> TaxRule:
    data = _object(value, "rule")
    _exact_keys(data, _RULE_KEYS, "rule")
    tax_year_value = data["tax_year"]
    if isinstance(tax_year_value, bool) or not isinstance(tax_year_value, int):
        raise PolicyValidationError("tax_year must be an int")
    try:
        tax_year = TaxYear(tax_year_value)
    except ValueError as exc:
        raise PolicyValidationError("invalid tax_year") from exc
    parameters = _object(data["parameters"], "parameters")
    effective_from = _date(data["effective_from"], "effective_from")
    effective_to = _date(data["effective_to"], "effective_to", nullable=True)
    effective_from = cast(date, effective_from)
    if effective_to is not None and effective_to < effective_from:
        raise PolicyValidationError("effective_to precedes effective_from")
    return TaxRule(
        rule_id=_string(data["rule_id"], "rule_id") or "",
        version=_string(data["version"], "version") or "",
        tax_year=tax_year,
        effective_from=effective_from,
        effective_to=effective_to,
        status=_enum(RuleStatus, data["status"], "status"),
        source_id=_string(data["source_id"], "source_id", nullable=True),
        verified_at=_date(data["verified_at"], "verified_at", nullable=True),
        parameters=freeze(parameters),
        supplementary_source_ids=_string_list(
            data["supplementary_source_ids"], "supplementary_source_ids"
        ),
        review_notes=_string_list(data["review_notes"], "review_notes"),
    )


def parse_rule_pack(text: str) -> RulePack:
    """Parse JSON without permitting binary floats, non-finite numbers, or loose fields."""
    try:
        raw = json.loads(text, parse_float=_reject_float, parse_constant=_reject_constant)
    except (json.JSONDecodeError, TypeError) as exc:
        raise PolicyValidationError(f"invalid JSON: {exc}") from exc
    data = _object(raw, "rule pack")
    _exact_keys(data, _TOP_KEYS, "rule pack")
    if data["schema_version"] != _SCHEMA_VERSION:
        raise PolicyValidationError("unsupported schema_version")
    tax_year_value = data["tax_year"]
    if isinstance(tax_year_value, bool) or not isinstance(tax_year_value, int):
        raise PolicyValidationError("tax_year must be an int")
    try:
        tax_year = TaxYear(tax_year_value)
    except ValueError as exc:
        raise PolicyValidationError("invalid tax_year") from exc
    sources_raw = data["sources"]
    rules_raw = data["rules"]
    if not isinstance(sources_raw, list):
        raise PolicyValidationError("sources must be a list")
    if not isinstance(rules_raw, list):
        raise PolicyValidationError("rules must be a list")
    sources = tuple(_source(source) for source in sources_raw)
    rules = tuple(_rule(rule) for rule in rules_raw)
    _reject_duplicates((source.source_id for source in sources), "source_id")
    _reject_duplicates((rule.rule_id for rule in rules), "rule_id")
    return RulePack(
        schema_version=_string(data["schema_version"], "schema_version") or "",
        rule_pack_id=_string(data["rule_pack_id"], "rule_pack_id") or "",
        version=_string(data["version"], "version") or "",
        description=_string(data["description"], "description") or "",
        jurisdiction=_string(data["jurisdiction"], "jurisdiction") or "",
        tax_year=tax_year,
        currency=_string(data["currency"], "currency") or "",
        status=_enum(RuleStatus, data["status"], "status"),
        sources=sources,
        rules=rules,
    )


def _reject_float(value: str) -> Never:
    raise PolicyValidationError(f"float is not allowed in policy JSON: {value}")


def _reject_duplicates(values: Iterable[str], field: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise PolicyValidationError(f"duplicate {field}: {value}")
        seen.add(value)


def rule_pack_to_dict(pack: RulePack) -> dict[str, object]:
    return {
        "schema_version": pack.schema_version,
        "rule_pack_id": pack.rule_pack_id,
        "version": pack.version,
        "description": pack.description,
        "jurisdiction": pack.jurisdiction,
        "tax_year": pack.tax_year.gregorian,
        "currency": pack.currency,
        "status": pack.status.value,
        "sources": [
            {
                "source_id": source.source_id,
                "title": source.title,
                "publisher": source.publisher,
                "authority": source.authority.value,
                "url": source.url,
                "published_at": source.published_at.isoformat() if source.published_at else None,
                "retrieved_at": source.retrieved_at.isoformat(),
            }
            for source in pack.sources
        ],
        "rules": [
            {
                "rule_id": rule.rule_id,
                "version": rule.version,
                "tax_year": rule.tax_year.gregorian,
                "effective_from": rule.effective_from.isoformat(),
                "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
                "status": rule.status.value,
                "source_id": rule.source_id,
                "verified_at": rule.verified_at.isoformat() if rule.verified_at else None,
                "parameters": thaw(rule.parameters),
                "supplementary_source_ids": list(rule.supplementary_source_ids),
                "review_notes": list(rule.review_notes),
            }
            for rule in pack.rules
        ],
    }


def rule_pack_content_hash(pack: RulePack) -> str:
    return sha256_hex(canonical_json(rule_pack_to_dict(pack)))


def load_bundled_rule_pack(rule_pack_id: str = BUNDLED_PACK_ID_2026) -> RulePack:
    if rule_pack_id != BUNDLED_PACK_ID_2026:
        raise PolicyValidationError(f"unknown bundled rule pack: {rule_pack_id}")
    resource = files("tax_gps.policy.packs").joinpath(f"{rule_pack_id}.json")
    return parse_rule_pack(resource.read_text(encoding="utf-8"))
