"""C02A-AC02/08: inconsistent wages and malformed policy fail closed."""

from dataclasses import replace

import pytest

from tax_gps.calculation.pvd import calculate_pvd
from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.engine import calculate_tax
from tests.acceptance.test_c02a_pvd import normal_profile
from tests.support.policy import activate_dict, bundled_pack_dict, production_pack, rule_dict


@pytest.mark.parametrize("wage", [0, 180001])
def test_c02a_conflicting_wage_is_not_a_partial_tax_result(wage: int) -> None:
    user = normal_profile()
    assert user.benefits.pvd is not None
    user = replace(
        user,
        benefits=replace(user.benefits, pvd=replace(user.benefits.pvd, wage_basis=Money.of(wage))),
    )
    with pytest.raises(InvalidValueError, match=r"pvd\.wage_basis") as error:
        calculate_tax(user, production_pack())
    assert "180001" not in str(error.value)


def test_c02a_split_rejects_negative_and_malformed_policy() -> None:
    with pytest.raises(InvalidValueError, match="negative"):
        calculate_pvd(Money.of(-1), production_pack())
    data = bundled_pack_dict()
    rule_dict(data, "PVD_ALLOWANCE")["parameters"]["maximum"] = True
    with pytest.raises(InvalidValueError, match="parameter"):
        calculate_pvd(Money.of(10000), activate_dict(data))
