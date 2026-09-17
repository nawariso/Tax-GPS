"""Catalog fixtures: the bundled 2026 opportunity catalog and mutated variants."""

import copy
import json
from functools import cache
from importlib.resources import files
from typing import Any

from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog, activate_catalog
from tax_gps.opportunity.loader import BUNDLED_CATALOG_ID_2026, parse_catalog

CatalogDict = dict[str, Any]


@cache
def _bundled_text() -> str:
    resource = files("tax_gps.opportunity.catalogs").joinpath(f"{BUNDLED_CATALOG_ID_2026}.json")
    return resource.read_text(encoding="utf-8")


def bundled_catalog_dict() -> CatalogDict:
    """A fresh, mutable copy of the bundled 2026 opportunity catalog."""
    data: CatalogDict = json.loads(_bundled_text())
    return copy.deepcopy(data)


def catalog_rule_dict(catalog: CatalogDict, rule_id: str) -> dict[str, Any]:
    for rule in catalog["rules"]:
        if rule["rule_id"] == rule_id:
            return rule  # type: ignore[no-any-return]
    raise KeyError(rule_id)


def catalog_definition_dict(catalog: CatalogDict, opportunity_id: str) -> dict[str, Any]:
    for definition in catalog["opportunities"]:
        if definition["opportunity_id"] == opportunity_id:
            return definition  # type: ignore[no-any-return]
    raise KeyError(opportunity_id)


def activate_catalog_dict(catalog: CatalogDict) -> ActivatedOpportunityCatalog:
    return activate_catalog(parse_catalog(json.dumps(catalog)))


@cache
def production_catalog() -> ActivatedOpportunityCatalog:
    """The bundled catalog exactly as shipped; artwork policy is deliberately not ready."""
    return activate_catalog_dict(bundled_catalog_dict())


def mark_rule_ready(catalog: CatalogDict, rule_id: str) -> CatalogDict:
    rule = catalog_rule_dict(catalog, rule_id)
    rule["status"] = "EFFECTIVE"
    rule["verified_at"] = "2026-09-16"
    return catalog


def mark_rule_unverified(catalog: CatalogDict, rule_id: str) -> CatalogDict:
    rule = catalog_rule_dict(catalog, rule_id)
    rule["status"] = "DRAFT"
    rule["verified_at"] = None
    return catalog


@cache
def artwork_ready_catalog() -> ActivatedOpportunityCatalog:
    """Test-only catalog in which the artwork policy rule has been governed as ready.

    The bundled production catalog never asserts this; readiness is catalog-derived so both
    states are exercised without falsely activating an unverified legal citation.
    """
    catalog = mark_rule_ready(bundled_catalog_dict(), opportunity_ids.ARTWORK_RULE)
    catalog["version"] = "1.0.0-artwork-ready-fixture"
    for definition in catalog["opportunities"]:
        definition["catalog_version"] = catalog["version"]
    return activate_catalog_dict(catalog)


@cache
def solar_unverified_catalog() -> ActivatedOpportunityCatalog:
    catalog = mark_rule_unverified(bundled_catalog_dict(), opportunity_ids.SOLAR_ROOFTOP_RULE)
    catalog["version"] = "1.0.0-solar-unverified-fixture"
    for definition in catalog["opportunities"]:
        definition["catalog_version"] = catalog["version"]
    return activate_catalog_dict(catalog)


@cache
def solar_ready_catalog() -> ActivatedOpportunityCatalog:
    """Test-only catalog for exercising gates after complete legal verification."""
    catalog = mark_rule_ready(bundled_catalog_dict(), opportunity_ids.SOLAR_ROOFTOP_RULE)
    catalog["version"] = "1.0.0-solar-ready-fixture"
    for definition in catalog["opportunities"]:
        definition["catalog_version"] = catalog["version"]
    return activate_catalog_dict(catalog)
