"""Opportunity catalog loading, governance, readiness, and immutability."""

import json
from dataclasses import FrozenInstanceError, replace
from datetime import date
from types import MappingProxyType

import pytest

from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.activation import CatalogActivationError, activate_catalog
from tax_gps.opportunity.loader import (
    BUNDLED_CATALOG_ID_2026,
    load_bundled_catalog,
    parse_catalog,
)
from tax_gps.opportunity.models import (
    OpportunityCategory,
    OpportunityStatus,
    OpportunityType,
)
from tax_gps.opportunity.readiness import evaluate_opportunity_readiness
from tax_gps.policy.loader import PolicyValidationError
from tax_gps.policy.models import RuleStatus
from tax_gps.policy.readiness import ReadinessCode
from tests.support.catalog import (
    activate_catalog_dict,
    bundled_catalog_dict,
    catalog_definition_dict,
    catalog_rule_dict,
    mark_rule_ready,
    mark_rule_unverified,
    production_catalog,
)
from tests.support.policy import production_pack


def test_bundled_catalog_loads_with_expected_identity() -> None:
    catalog = load_bundled_catalog()
    assert catalog.catalog_id == BUNDLED_CATALOG_ID_2026
    assert catalog.tax_year == TaxYear(2026)
    assert catalog.currency == "THB"
    assert catalog.jurisdiction == "TH"
    assert catalog.status is RuleStatus.EFFECTIVE


@pytest.mark.negative
def test_unknown_bundled_catalog_is_rejected() -> None:
    with pytest.raises(PolicyValidationError, match="unknown bundled catalog"):
        load_bundled_catalog("TH-OPP-9999-001")


def test_catalog_declares_every_required_existing_right_in_stable_order() -> None:
    catalog = production_catalog().catalog
    rights = [
        definition.opportunity_id
        for definition in catalog.definitions
        if definition.opportunity_type is OpportunityType.EXISTING_RIGHT
    ]
    assert rights == list(opportunity_ids.EXISTING_RIGHT_IDS)
    assert all(
        catalog.definition(right).category is OpportunityCategory.CLAIM_EXISTING_RIGHT
        for right in rights
    )
    assert not any(catalog.definition(right).requires_new_cash for right in rights)


def test_catalog_orders_existing_rights_before_new_cash_opportunities() -> None:
    types = [definition.opportunity_type for definition in production_catalog().catalog.definitions]
    assert types == sorted(types, key=lambda item: item is OpportunityType.NEW_CASH)
    assert OpportunityType.NEW_CASH in types


def test_thai_esg_definition_carries_governed_metadata() -> None:
    definition = production_catalog().catalog.definition(opportunity_ids.THAI_ESG)
    assert definition.category is OpportunityCategory.INVESTMENT_TAX
    assert definition.opportunity_type is OpportunityType.NEW_CASH
    assert definition.requires_new_cash is True
    assert definition.intrinsic_need_required is False
    assert definition.standalone_limit == Money.of(300000)
    assert definition.shared_limit_group == opportunity_ids.THAI_ESG_2026_POOL
    assert definition.lockup_metadata is not None
    assert definition.lockup_metadata.minimum_holding_years == 5
    assert definition.evidence_requirements
    assert definition.catalog_version == production_catalog().version


def test_artwork_definition_carries_governed_metadata() -> None:
    definition = production_catalog().catalog.definition(opportunity_ids.ARTWORK)
    assert definition.category is OpportunityCategory.LIFESTYLE_INTENT
    assert definition.requires_new_cash is True
    assert definition.intrinsic_need_required is True
    assert definition.standalone_limit == Money.of(100000)
    assert definition.shared_limit_group is None
    assert definition.effective_from == date(2025, 1, 1)
    assert definition.effective_to == date(2027, 12, 31)
    assert definition.evidence_requirements


def test_solar_definition_matches_the_royal_decree_period_and_cap() -> None:
    definition = production_catalog().catalog.definition(opportunity_ids.SOLAR_ROOFTOP)
    assert definition.category is OpportunityCategory.UTILITY_INVESTMENT
    assert definition.intrinsic_need_required is True
    assert definition.standalone_limit == Money.of(200000)
    assert definition.effective_from == date(2026, 3, 3)
    assert definition.effective_to == date(2028, 12, 31)


def test_thai_esg_and_thai_esgx_share_one_pool_and_expose_no_independent_cap() -> None:
    catalog = production_catalog().catalog
    rule = catalog.rule(opportunity_ids.THAI_ESG_RULE)
    assert isinstance(rule.parameters, MappingProxyType)
    assert rule.parameters["shared_group_id"] == opportunity_ids.THAI_ESG_2026_POOL
    assert rule.parameters["assessable_income_rate"] == "0.30"
    assert rule.parameters["cap"] == "300000.00"
    assert rule.parameters["minimum_holding_years"] == 5
    shared = [
        definition.opportunity_id
        for definition in catalog.definitions
        if definition.shared_limit_group == opportunity_ids.THAI_ESG_2026_POOL
    ]
    assert shared == [opportunity_ids.THAI_ESG]


def test_definitions_are_immutable_hashable_and_canonically_serializable() -> None:
    definition = production_catalog().catalog.definition(opportunity_ids.THAI_ESG)
    assert hash(definition) == hash(
        production_catalog().catalog.definition(opportunity_ids.THAI_ESG)
    )
    assert len(definition.content_hash()) == 64
    data = definition.to_dict()
    assert data["type"] == OpportunityType.NEW_CASH.value
    assert data["standalone_limit"] == "300000.00"
    with pytest.raises(FrozenInstanceError):
        definition.name = "changed"  # type: ignore[misc]


def test_catalog_content_hash_changes_with_material_content() -> None:
    catalog = bundled_catalog_dict()
    first = activate_catalog_dict(catalog).content_hash
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["name"] = "renamed"
    assert activate_catalog_dict(catalog).content_hash != first


@pytest.mark.mandatory
def test_disc_17_unverified_policy_rule_is_not_ready() -> None:
    catalog = activate_catalog_dict(
        mark_rule_unverified(bundled_catalog_dict(), opportunity_ids.THAI_ESG_RULE)
    ).catalog
    readiness = evaluate_opportunity_readiness(
        catalog.definition(opportunity_ids.THAI_ESG), catalog, production_pack()
    )
    assert not readiness.ready
    assert {finding.code for finding in readiness.findings} == {
        ReadinessCode.RULE_NOT_EFFECTIVE,
        ReadinessCode.RULE_NOT_VERIFIED,
    }


def test_bundled_artwork_policy_is_explicitly_not_ready_and_becomes_ready_when_governed() -> None:
    catalog = production_catalog().catalog
    definition = catalog.definition(opportunity_ids.ARTWORK)
    assert not evaluate_opportunity_readiness(definition, catalog, production_pack()).ready
    ready = activate_catalog_dict(
        mark_rule_ready(bundled_catalog_dict(), opportunity_ids.ARTWORK_RULE)
    ).catalog
    assert evaluate_opportunity_readiness(
        ready.definition(opportunity_ids.ARTWORK), ready, production_pack()
    ).ready


def test_bundled_solar_policy_is_not_ready_when_all_decree_conditions_are_not_verified() -> None:
    catalog = production_catalog().catalog
    readiness = evaluate_opportunity_readiness(
        catalog.definition(opportunity_ids.SOLAR_ROOFTOP), catalog, production_pack()
    )
    assert not readiness.ready
    assert {finding.code for finding in readiness.findings} == {
        ReadinessCode.RULE_NOT_EFFECTIVE,
        ReadinessCode.RULE_NOT_VERIFIED,
    }


def test_existing_right_rules_resolve_against_the_activated_policy_pack() -> None:
    catalog = production_catalog().catalog
    for right_id in opportunity_ids.EXISTING_RIGHT_IDS:
        definition = catalog.definition(right_id)
        assert definition.rule_ids
        assert evaluate_opportunity_readiness(definition, catalog, production_pack()).ready


@pytest.mark.negative
def test_readiness_reports_missing_unresolved_and_non_authoritative_sources() -> None:
    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["rule_ids"] = [
        opportunity_ids.THAI_ESG_RULE,
        "TH-OPP-RULE-MISSING",
    ]
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.REQUIRED_RULE_MISSING in {f.code for f in readiness.findings}

    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["source_id"] = None
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.RULE_SOURCE_MISSING in {f.code for f in readiness.findings}

    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["source_id"] = "NOPE"
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.RULE_SOURCE_UNRESOLVED in {f.code for f in readiness.findings}


@pytest.mark.negative
def test_readiness_rejects_unresolved_declared_sources_and_tax_year_drift() -> None:
    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["source_ids"] = ["NOPE"]
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.RULE_SOURCE_UNRESOLVED in {f.code for f in readiness.findings}

    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["tax_year"] = 2025
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.RULE_TAX_YEAR_MISMATCH in {f.code for f in readiness.findings}


@pytest.mark.negative
def test_non_authoritative_catalog_source_is_rejected_by_readiness() -> None:
    catalog = bundled_catalog_dict()
    for source in catalog["sources"]:
        if source["source_id"] == "SEC-THAI-ESG-2026":
            source["url"] = "http://example.com/blog"
            source["authority"] = "GOVERNMENT_AUTHORITY"
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.SOURCE_NOT_AUTHORITATIVE in {f.code for f in readiness.findings}


@pytest.mark.negative
def test_catalog_activation_rejects_structurally_unusable_catalogs() -> None:
    catalog = bundled_catalog_dict()
    catalog["status"] = "DRAFT"
    with pytest.raises(CatalogActivationError, match="CATALOG_NOT_EFFECTIVE"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog["currency"] = "USD"
    with pytest.raises(CatalogActivationError, match="CURRENCY"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog["jurisdiction"] = "SG"
    with pytest.raises(CatalogActivationError, match="JURISDICTION"):
        activate_catalog_dict(catalog)


@pytest.mark.negative
def test_catalog_loader_rejects_malformed_documents() -> None:
    with pytest.raises(PolicyValidationError, match="invalid JSON"):
        parse_catalog("{")
    catalog = bundled_catalog_dict()
    catalog["schema_version"] = "2"
    with pytest.raises(PolicyValidationError, match="unsupported schema_version"):
        parse_catalog(json.dumps(catalog))
    catalog = bundled_catalog_dict()
    catalog_with_float = json.dumps(catalog).replace('"300000.00"', "300000.5")
    with pytest.raises(PolicyValidationError, match="float is not allowed"):
        parse_catalog(catalog_with_float)
    catalog = bundled_catalog_dict()
    catalog["surprise"] = 1
    with pytest.raises(PolicyValidationError, match="unknown key"):
        parse_catalog(json.dumps(catalog))
    catalog = bundled_catalog_dict()
    catalog["opportunities"].append(catalog["opportunities"][0])
    with pytest.raises(PolicyValidationError, match="duplicate opportunity_id"):
        parse_catalog(json.dumps(catalog))


@pytest.mark.negative
def test_catalog_loader_rejects_malformed_opportunity_entries() -> None:
    catalog = bundled_catalog_dict()
    catalog["opportunities"] = {}
    with pytest.raises(PolicyValidationError, match="opportunities must be a list"):
        parse_catalog(json.dumps(catalog))

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["category"] = "NOT_A_CATEGORY"
    with pytest.raises(PolicyValidationError, match="unknown category"):
        parse_catalog(json.dumps(catalog))

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["requires_new_cash"] = "yes"
    with pytest.raises(PolicyValidationError, match="requires_new_cash must be a boolean"):
        parse_catalog(json.dumps(catalog))

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.ARTWORK)["effective_to"] = "2024-01-01"
    with pytest.raises(PolicyValidationError, match="effective_to precedes effective_from"):
        parse_catalog(json.dumps(catalog))

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["evidence_requirements"] = [1]
    with pytest.raises(PolicyValidationError, match="evidence requirement must be an object"):
        parse_catalog(json.dumps(catalog))


@pytest.mark.negative
@pytest.mark.parametrize(
    "case",
    [
        pytest.param("invalid_constant"),
        pytest.param("missing_key"),
        pytest.param("string_type"),
        pytest.param("invalid_date"),
        pytest.param("string_list"),
        pytest.param("unknown_authority"),
        pytest.param("unknown_status"),
        pytest.param("rule_year"),
        pytest.param("rule_period"),
        pytest.param("unknown_type"),
        pytest.param("lockup_years"),
        pytest.param("evidence_list"),
        pytest.param("catalog_version"),
        pytest.param("catalog_year"),
        pytest.param("sources_list"),
        pytest.param("rules_list"),
    ],
)
def test_catalog_loader_rejects_each_strict_schema_violation(case: str) -> None:  # noqa: PLR0912
    if case == "invalid_constant":
        text = "NaN"
    else:
        catalog = bundled_catalog_dict()
        thai_esg = catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)
        rule = catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)
        if case == "missing_key":
            del catalog["description"]
        elif case == "string_type":
            catalog["version"] = 1
        elif case == "invalid_date":
            rule["effective_from"] = "not-a-date"
        elif case == "string_list":
            rule["supplementary_source_ids"] = [1]
        elif case == "unknown_authority":
            catalog["sources"][0]["authority"] = "UNKNOWN"
        elif case == "unknown_status":
            catalog["status"] = "UNKNOWN"
        elif case == "rule_year":
            rule["tax_year"] = True
        elif case == "rule_period":
            rule["effective_to"] = "2025-12-31"
        elif case == "unknown_type":
            thai_esg["type"] = "UNKNOWN"
        elif case == "lockup_years":
            thai_esg["lockup_metadata"]["minimum_holding_years"] = True
        elif case == "evidence_list":
            thai_esg["evidence_requirements"] = {}
        elif case == "catalog_version":
            thai_esg["catalog_version"] = "wrong"
        elif case == "catalog_year":
            catalog["tax_year"] = True
        elif case == "sources_list":
            catalog["sources"] = {}
        else:
            catalog["rules"] = {}
        text = json.dumps(catalog)
    with pytest.raises(PolicyValidationError):
        parse_catalog(text)


@pytest.mark.negative
def test_readiness_checks_supplementary_source_resolution_and_authority() -> None:
    catalog = bundled_catalog_dict()
    rule = catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)
    rule["supplementary_source_ids"] = ["NOPE"]
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.RULE_SOURCE_UNRESOLVED in {item.code for item in readiness.findings}

    catalog = bundled_catalog_dict()
    catalog["sources"].append(
        {
            "source_id": "BLOG",
            "title": "Blog",
            "publisher": "Unknown",
            "authority": "GOVERNMENT_AUTHORITY",
            "url": "https://example.com/blog",
            "published_at": None,
            "retrieved_at": "2026-09-16",
        }
    )
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["supplementary_source_ids"] = ["BLOG"]
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.SOURCE_NOT_AUTHORITATIVE in {item.code for item in readiness.findings}


@pytest.mark.negative
def test_catalog_lookup_failures_are_explicit() -> None:
    catalog = production_catalog().catalog
    assert catalog.find_definition("NOPE") is None
    assert catalog.find_rule("NOPE") is None
    assert catalog.find_source("NOPE") is None
    with pytest.raises(KeyError):
        catalog.definition("NOPE")
    with pytest.raises(KeyError):
        catalog.rule("NOPE")


def test_enums_cover_the_specified_vocabularies() -> None:
    assert {item.value for item in OpportunityType} == {"EXISTING_RIGHT", "NEW_CASH"}
    assert {item.value for item in OpportunityCategory} == {
        "CLAIM_EXISTING_RIGHT",
        "INVESTMENT_TAX",
        "LIFESTYLE_INTENT",
        "UTILITY_INVESTMENT",
    }
    assert {item.value for item in OpportunityStatus} == {
        "AVAILABLE",
        "INELIGIBLE",
        "REQUIRES_INPUT",
        "RULE_NOT_READY",
        "OUTSIDE_EFFECTIVE_PERIOD",
    }


def test_activated_catalog_exposes_identity_for_replay() -> None:
    activated = production_catalog()
    assert activated.catalog_id == BUNDLED_CATALOG_ID_2026
    assert activated.version == activated.catalog.version
    assert len(activated.content_hash) == 64
    assert activate_catalog(activated.catalog).content_hash == activated.content_hash


@pytest.mark.negative
def test_activation_rejects_missing_required_definitions_and_dependencies() -> None:
    catalog = bundled_catalog_dict()
    catalog["opportunities"] = [
        item
        for item in catalog["opportunities"]
        if item["opportunity_id"] != opportunity_ids.PERSONAL_ALLOWANCE
    ]
    with pytest.raises(CatalogActivationError, match="REQUIRED_DEFINITION_MISSING"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.ARTWORK)["rule_ids"] = []
    with pytest.raises(CatalogActivationError, match="RULE_DEPENDENCY_MISSING"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog["opportunities"] = [
        item
        for item in catalog["opportunities"]
        if item["opportunity_id"] != opportunity_ids.ARTWORK
    ]
    with pytest.raises(CatalogActivationError, match="REQUIRED_DEFINITION_MISSING"):
        activate_catalog_dict(catalog)


@pytest.mark.negative
def test_activation_rejects_conflicting_capacity_metadata() -> None:
    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["standalone_limit"] = "900000.00"
    with pytest.raises(CatalogActivationError, match="CAPACITY_METADATA_MISMATCH"):
        activate_catalog_dict(catalog)


@pytest.mark.negative
def test_activation_skips_new_cash_rule_checks_for_a_missing_definition() -> None:
    catalog = bundled_catalog_dict()
    catalog["opportunities"] = [
        item
        for item in catalog["opportunities"]
        if item["opportunity_id"] != opportunity_ids.ARTWORK
    ]
    with pytest.raises(CatalogActivationError) as excinfo:
        activate_catalog_dict(catalog)
    message = str(excinfo.value)
    assert f"REQUIRED_DEFINITION_MISSING:{opportunity_ids.ARTWORK}" in message
    assert f"CAPACITY_METADATA_MISMATCH:{opportunity_ids.ARTWORK}" not in message


@pytest.mark.negative
def test_activation_rejects_rule_identity_group_and_intent_contract_conflicts() -> None:
    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.THAI_ESG)["rule_ids"] = [
        opportunity_ids.ARTWORK_RULE
    ]
    with pytest.raises(CatalogActivationError, match="REQUIRED_RULE_MISSING"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog["rules"] = [
        rule for rule in catalog["rules"] if rule["rule_id"] != opportunity_ids.THAI_ESG_RULE
    ]
    with pytest.raises(CatalogActivationError, match="REQUIRED_RULE_MISSING"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["parameters"]["cap"] = 300000
    with pytest.raises(CatalogActivationError, match="CAPACITY_METADATA_MISMATCH"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["parameters"]["shared_group_id"] = (
        "OTHER"
    )
    with pytest.raises(CatalogActivationError, match="SHARED_GROUP_METADATA_MISMATCH"):
        activate_catalog_dict(catalog)

    catalog = bundled_catalog_dict()
    catalog_definition_dict(catalog, opportunity_ids.ARTWORK)["intrinsic_need_required"] = False
    with pytest.raises(CatalogActivationError, match="INTRINSIC_INTENT_GATE_MISSING"):
        activate_catalog_dict(catalog)


@pytest.mark.negative
def test_readiness_rejects_missing_rules_and_conflicting_cross_catalog_sources() -> None:
    catalog = production_catalog().catalog
    definition = replace(catalog.definition(opportunity_ids.THAI_ESG), rule_ids=())
    readiness = evaluate_opportunity_readiness(definition, catalog, production_pack())
    assert ReadinessCode.REQUIRED_RULE_MISSING in {item.code for item in readiness.findings}

    pack_source = production_pack().pack.sources[0]
    conflicting_source = replace(pack_source, title=f"{pack_source.title} conflict")
    conflicting_catalog = replace(catalog, sources=(*catalog.sources, conflicting_source))
    definition = replace(definition, source_ids=(*definition.source_ids, pack_source.source_id))
    readiness = evaluate_opportunity_readiness(definition, conflicting_catalog, production_pack())
    assert ReadinessCode.RULE_SOURCE_UNRESOLVED in {item.code for item in readiness.findings}


@pytest.mark.negative
def test_readiness_rejects_rule_period_and_arbitrary_official_provider_host() -> None:
    catalog = bundled_catalog_dict()
    catalog_rule_dict(catalog, opportunity_ids.THAI_ESG_RULE)["effective_from"] = "2026-12-01"
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG),
        activated,
        production_pack(),
        planning_date=date(2026, 9, 16),
    )
    assert ReadinessCode.RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR in {
        item.code for item in readiness.findings
    }

    catalog = bundled_catalog_dict()
    catalog["sources"][0]["url"] = "https://example.com/blog"
    activated = activate_catalog_dict(catalog).catalog
    readiness = evaluate_opportunity_readiness(
        activated.definition(opportunity_ids.THAI_ESG), activated, production_pack()
    )
    assert ReadinessCode.SOURCE_NOT_AUTHORITATIVE in {item.code for item in readiness.findings}
