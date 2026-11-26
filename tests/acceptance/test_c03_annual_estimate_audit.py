"""C03-AC04,06,09: replay a downloaded annual snapshot and bind its material."""

import json
from dataclasses import replace
from datetime import date
from typing import Any, cast

import pytest

from tax_gps.audit import AuditReplayError
from tax_gps.calculation.annual_estimate_audit import (
    create_annual_estimate_snapshot,
    replay_annual_estimate,
)
from tax_gps.core.canonical import canonical_json, sha256_hex
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.opportunity.opportunity_ids import THAI_ESG_2026_POOL
from tax_gps.profile.models import Child, Parent, RetirementContribution, SharedLimitUsage
from tax_gps.profile.rmf import RmfFacts, RmfReportConfirmation, RmfReportingStatus
from tests.acceptance.test_c03_annual_estimate import (
    CUTOFF,
    base_input,
    fractional_input,
    pvd_input,
    rmf_input,
)
from tests.support.policy import production_pack


@pytest.mark.parametrize("scenario", ["complete", "partial", "pvd", "fractional", "rmf-confirmed"])
def test_c03_snapshot_replays_complete_and_partial_withholding(scenario: str) -> None:
    inputs = base_input()
    if scenario == "partial":
        inputs = replace(
            inputs,
            forecast=replace(inputs.forecast, withholding=None),
            shared_limit_usage=(SharedLimitUsage(THAI_ESG_2026_POOL, Money.zero()),),
            rights=replace(
                inputs.rights,
                retirement_contributions=(RetirementContribution("fixture", Money.zero()),),
            ),
        )
    elif scenario == "pvd":
        inputs = pvd_input()
    elif scenario == "fractional":
        inputs = fractional_input()
    elif scenario == "rmf-confirmed":
        inputs = rmf_input()
        rmf = cast(RmfFacts, inputs.rights.rmf)
        receipt = RmfReportConfirmation(
            cast(str, rmf.fund_name),
            cast(str, rmf.amc_name),
            TaxYear(2026),
            Money.of(100000),
            CUTOFF,
        )
        inputs = replace(
            inputs,
            rights=replace(
                inputs.rights,
                parents=(Parent("mother", True),),
                children=(Child("child", True, 2019, order=1),),
                rmf=replace(
                    rmf,
                    reporting_status=RmfReportingStatus.CONFIRMED_SUBMITTED,
                    report_confirmation=receipt,
                ),
            ),
        )
    pack = production_pack()
    snapshot = create_annual_estimate_snapshot(inputs, pack)
    payload = json.loads(canonical_json(snapshot.to_dict()))
    assert payload["schema"] == "tax-gps-annual-estimate/1"
    assert payload["pack"]["content_hash"] == pack.content_hash
    assert payload["material"]["actual"]["wages"] == "600000.00"
    assert payload["outputs"]["baseline_status"] == "READY"
    if scenario == "partial":
        assert payload["outputs"]["settlement_status"] == "REQUIRES_INPUT"
        assert payload["outputs"]["settlement_amount"] is None
        assert payload["outputs"]["withholding_missing_fact_ids"] == ["forecast.withholding"]
    if scenario == "fractional":
        assert payload["outputs"]["settlement_amount"] == "0.00105"
    assert replay_annual_estimate(payload, pack) == snapshot.result
    assert snapshot.to_dict() == payload
    payload["material"]["actual"]["wages"] = "1.00"
    assert snapshot.to_dict() != payload


@pytest.mark.parametrize(
    ("keys", "value"),
    [
        (("schema",), "version-older"),
        (("engine_version",), "tax-gps-core/0.3.0"),
        (("pack", "version"), "1.1.0"),
        (("pack", "rule_pack_id"), "other"),
        (("pack", "content_hash"), "unmatched"),
        (("material", "actual", "wages"), "599999.00"),
        (("material", "forecast", "withholding"), "2.00"),
        (("material", "cutoff_date"), "2026-10-30"),
        (("material", "rights", "personal_eligible"), "invalid"),
        (("material", "actual"), []),
        (("material", "rights", "parents"), {}),
        (("outputs", "settlement_amount"), "50.00"),
        (("snapshot_hash",), "5000"),
    ],
)
def test_c03_snapshot_rejects_changed_material_or_version(
    keys: tuple[str, ...], value: object
) -> None:
    pack = production_pack()
    payload: dict[str, Any] = create_annual_estimate_snapshot(base_input(), pack).to_dict()
    nested = payload
    for key in keys[:-1]:
        nested = nested[key]
    nested[keys[-1]] = value
    with pytest.raises(AuditReplayError):
        replay_annual_estimate(payload, pack)


def test_c03_snapshot_replay_compares_outputs_even_with_recomputed_hash() -> None:
    pack = production_pack()
    payload: dict[str, Any] = create_annual_estimate_snapshot(base_input(), pack).to_dict()
    payload["outputs"]["settlement_amount"] = "1.00"
    payload.pop("snapshot_hash")
    payload["snapshot_hash"] = sha256_hex(canonical_json(payload))
    with pytest.raises(AuditReplayError):
        replay_annual_estimate(payload, pack)


def test_c03_snapshot_rejects_sub_satang_material_before_recalculation() -> None:
    pack = production_pack()
    payload: dict[str, Any] = create_annual_estimate_snapshot(base_input(), pack).to_dict()
    payload["material"]["actual"]["withholding"] = "45000.001"
    with pytest.raises(AuditReplayError, match="invalid annual estimate snapshot"):
        replay_annual_estimate(payload, pack)


def test_c03_snapshot_distinguishes_two_periods_at_same_pit() -> None:
    request = base_input()
    pack = production_pack()
    old = create_annual_estimate_snapshot(request, pack).to_dict()
    changed = replace(
        request,
        actual=replace(request.actual, wages=Money.of(590000)),
        forecast=replace(request.forecast, wages=Money.of(310500)),
    )
    new = create_annual_estimate_snapshot(changed, pack).to_dict()
    assert old["outputs"] == new["outputs"]
    assert old["snapshot_hash"] != new["snapshot_hash"]


def test_c03_snapshot_requires_ready_baseline() -> None:
    request = replace(base_input(), confirmed_for=date(2026, 10, 30))
    with pytest.raises(AuditReplayError):
        create_annual_estimate_snapshot(request, production_pack())
