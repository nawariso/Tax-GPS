"""Production activation gate and identity for opportunity catalogs."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.errors import TaxCoreError
from tax_gps.core.money import Money
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.models import OpportunityCatalog
from tax_gps.policy.models import RuleStatus


class CatalogActivationError(TaxCoreError):
    """The catalog cannot be used for discovery."""


@dataclass(frozen=True, slots=True)
class ActivatedOpportunityCatalog:
    catalog: OpportunityCatalog
    content_hash: str

    @property
    def catalog_id(self) -> str:
        return self.catalog.catalog_id

    @property
    def version(self) -> str:
        return self.catalog.version


def catalog_to_dict(catalog: OpportunityCatalog) -> dict[str, object]:
    return {
        "schema_version": catalog.schema_version,
        "catalog_id": catalog.catalog_id,
        "version": catalog.version,
        "description": catalog.description,
        "jurisdiction": catalog.jurisdiction,
        "tax_year": catalog.tax_year.gregorian,
        "currency": catalog.currency,
        "status": catalog.status.value,
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
            for source in catalog.sources
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
                "parameters": rule.parameters,
                "supplementary_source_ids": list(rule.supplementary_source_ids),
                "review_notes": list(rule.review_notes),
            }
            for rule in catalog.rules
        ],
        "opportunities": [definition.to_dict() for definition in catalog.definitions],
    }


def _validate_new_cash_rules(catalog: OpportunityCatalog, findings: list[str]) -> None:
    for opportunity_id, expected_rule_id in opportunity_ids.NEW_CASH_RULE_BY_ID.items():
        definition = catalog.find_definition(opportunity_id)
        if definition is None:
            continue
        if not definition.rule_ids:
            findings.append(f"RULE_DEPENDENCY_MISSING:{opportunity_id}")
            continue
        if expected_rule_id not in definition.rule_ids:
            findings.append(f"REQUIRED_RULE_MISSING:{expected_rule_id}")
        rule = catalog.find_rule(expected_rule_id)
        if rule is None:
            findings.append(f"REQUIRED_RULE_MISSING:{expected_rule_id}")
            continue
        cap = rule.parameters.get("cap")
        if (
            not isinstance(cap, str)
            or definition.standalone_limit is None
            or Money.of(cap) != definition.standalone_limit
        ):
            findings.append(f"CAPACITY_METADATA_MISMATCH:{opportunity_id}")
        governed_group = rule.parameters.get("shared_group_id")
        if governed_group != definition.shared_limit_group:
            findings.append(f"SHARED_GROUP_METADATA_MISMATCH:{opportunity_id}")


def _validate_intrinsic_intent_gates(catalog: OpportunityCatalog, findings: list[str]) -> None:
    for opportunity_id in (opportunity_ids.ARTWORK, opportunity_ids.SOLAR_ROOFTOP):
        definition = catalog.find_definition(opportunity_id)
        if definition is not None and not definition.intrinsic_need_required:
            findings.append(f"INTRINSIC_INTENT_GATE_MISSING:{opportunity_id}")


def activate_catalog(catalog: OpportunityCatalog) -> ActivatedOpportunityCatalog:
    findings: list[str] = []
    if catalog.status is not RuleStatus.EFFECTIVE:
        findings.append("CATALOG_NOT_EFFECTIVE")
    if catalog.currency != "THB":
        findings.append("CATALOG_CURRENCY_UNSUPPORTED")
    if catalog.jurisdiction != "TH":
        findings.append("CATALOG_JURISDICTION_UNSUPPORTED")
    present = {definition.opportunity_id for definition in catalog.definitions}
    for required in opportunity_ids.ALL_DEFINITION_IDS:
        if required not in present:
            findings.append(f"REQUIRED_DEFINITION_MISSING:{required}")
    _validate_new_cash_rules(catalog, findings)
    _validate_intrinsic_intent_gates(catalog, findings)
    if findings:
        raise CatalogActivationError("; ".join(findings))
    return ActivatedOpportunityCatalog(
        catalog, sha256_hex(canonical_json(catalog_to_dict(catalog)))
    )
