"""PVD split, driven by the selected activated rule pack."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from tax_gps.core.canonical import JsonValue
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.policy.activation import ActivatedRulePack


def pvd_parameter(pack: ActivatedRulePack, rule_id: str, name: str) -> str:
    value = cast(Mapping[str, JsonValue], pack.pack.rule(rule_id).parameters)[name]
    if not isinstance(value, str):
        raise InvalidValueError("PVD policy parameter must be decimal text")
    return value


@dataclass(frozen=True, slots=True)
class PvdCalculation:
    employee_paid: Money
    allowance: Money
    exemption: Money
    excess: Money

    def to_dict(self) -> dict[str, object]:
        return {
            name: getattr(self, name).canonical()
            for name in ("employee_paid", "allowance", "exemption", "excess")
        }


def calculate_pvd(employee_paid: Money, pack: ActivatedRulePack) -> PvdCalculation:
    if employee_paid.is_negative():
        raise InvalidValueError("pvd.employee_paid cannot be negative")
    allowance = Money.min(employee_paid, Money.of(pvd_parameter(pack, "PVD_ALLOWANCE", "maximum")))
    exemption = Money.min(
        (employee_paid - allowance).floor_at_zero(),
        Money.of(pvd_parameter(pack, "PVD_EXEMPTION", "maximum")),
    )
    return PvdCalculation(
        employee_paid, allowance, exemption, employee_paid - allowance - exemption
    )
