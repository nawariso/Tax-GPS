"""Discovery audit snapshot and deterministic replay acceptance."""

from dataclasses import replace
from datetime import date

import pytest

from tax_gps.calculation.models import TaxState
from tax_gps.core.canonical import thaw
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.discovery.audit import (
    DiscoveryReplayError,
    create_discovery_snapshot,
    replay_discovery,
)
from tax_gps.discovery.context import DiscoveryContext
from tax_gps.discovery.engine import DISCOVERY_ENGINE_VERSION, discover_opportunities
from tax_gps.engine import calculate_tax
from tax_gps.opportunity.activation import ActivatedOpportunityCatalog
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.profile.models import IncomeProfile, UserProfile
from tests.support.catalog import activate_catalog_dict, bundled_catalog_dict, production_catalog
from tests.support.policy import activate_dict, bundled_pack_dict, production_pack


def profile(salary: int = 800000) -> UserProfile:
    return UserProfile(
        "replay",
        "1",
        TaxYear(2026),
        IncomeProfile(Money.of(salary)),
    )


def inputs() -> tuple[
    UserProfile,
    TaxState,
    ActivatedRulePack,
    ActivatedOpportunityCatalog,
    DiscoveryContext,
]:
    user = profile()
    pack = production_pack()
    catalog = production_catalog()
    state = calculate_tax(user, pack)
    context = DiscoveryContext(TaxYear(2026), date(2026, 9, 16))
    return user, state, pack, catalog, context


@pytest.mark.mandatory
@pytest.mark.replay
def test_disc_18_identical_material_inputs_reproduce_the_result_and_hash() -> None:
    user, state, pack, catalog, context = inputs()
    result = discover_opportunities(user, state, pack, catalog, context)
    snapshot = create_discovery_snapshot(user, state, pack, catalog, context, result)

    replayed = replay_discovery(snapshot, user, state, pack, catalog, context)

    assert replayed == result
    assert replayed.discovery_hash == snapshot.discovery_hash
    assert thaw(snapshot.discovery_output) == result.to_dict()
    assert snapshot.profile_hash == user.profile_hash()
    assert snapshot.tax_state_hash == state.output_hash
    assert snapshot.rule_pack_hash == pack.content_hash
    assert snapshot.opportunity_catalog_hash == catalog.content_hash


@pytest.mark.mandatory
@pytest.mark.replay
@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("profile", "profile"),
        ("tax_state", "tax state"),
        ("policy", "rule pack"),
        ("catalog", "catalog"),
        ("planning_date", "context"),
        ("engine_version", "engine version"),
    ],
)
def test_disc_19_changing_any_material_replay_input_is_rejected(change: str, message: str) -> None:
    user, state, pack, catalog, context = inputs()
    result = discover_opportunities(user, state, pack, catalog, context)
    snapshot = create_discovery_snapshot(user, state, pack, catalog, context, result)
    engine_version = DISCOVERY_ENGINE_VERSION

    if change == "profile":
        user = replace(user, version="2")
    elif change == "tax_state":
        state = calculate_tax(profile(900000), pack)
    elif change == "policy":
        raw = bundled_pack_dict()
        raw["version"] = "changed"
        pack = activate_dict(raw)
    elif change == "catalog":
        raw = bundled_catalog_dict()
        raw["description"] = "changed"
        catalog = activate_catalog_dict(raw)
    elif change == "planning_date":
        context = DiscoveryContext(TaxYear(2026), date(2026, 9, 17))
    else:
        engine_version = "tax-gps-discovery/changed"

    with pytest.raises(DiscoveryReplayError, match=message):
        replay_discovery(
            snapshot,
            user,
            state,
            pack,
            catalog,
            context,
            engine_version=engine_version,
        )


def test_discovery_snapshot_is_immutable() -> None:
    user, state, pack, catalog, context = inputs()
    result = discover_opportunities(user, state, pack, catalog, context)
    snapshot = create_discovery_snapshot(user, state, pack, catalog, context, result)
    with pytest.raises((AttributeError, TypeError)):
        snapshot.discovery_hash = "changed"  # type: ignore[misc]


@pytest.mark.negative
def test_snapshot_creation_rejects_an_unhashed_result() -> None:
    user, state, pack, catalog, context = inputs()
    result = discover_opportunities(user, state, pack, catalog, context)
    with pytest.raises(ValueError, match="must be hashed"):
        create_discovery_snapshot(
            user,
            state,
            pack,
            catalog,
            context,
            replace(result, discovery_hash=""),
        )


@pytest.mark.negative
def test_replay_rejects_hash_and_serialized_output_tampering() -> None:
    user, state, pack, catalog, context = inputs()
    result = discover_opportunities(user, state, pack, catalog, context)
    snapshot = create_discovery_snapshot(user, state, pack, catalog, context, result)

    with pytest.raises(DiscoveryReplayError, match="output hash"):
        replay_discovery(
            replace(snapshot, discovery_hash="changed"),
            user,
            state,
            pack,
            catalog,
            context,
        )
    with pytest.raises(DiscoveryReplayError, match="output does not match"):
        replay_discovery(
            replace(snapshot, discovery_output="changed"),
            user,
            state,
            pack,
            catalog,
            context,
        )
