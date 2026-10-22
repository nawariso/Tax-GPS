"""C02A-AC01/02: malformed facts fail privately, immutable canonical facts."""

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money
from tax_gps.profile.pvd import FundHistoryFacts, OtherRightsFacts, PvdFacts, facts_to_dict


@pytest.mark.parametrize("name", ["employee_paid", "wage_basis"])
@pytest.mark.parametrize("value", ["secret", Money.of(-1)])
def test_c02a_invalid_money_fact(name: str, value: Any) -> None:
    with pytest.raises(InvalidValueError) as error:
        PvdFacts(**{name: value})
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("value", ["", " ", 1])
def test_c02a_fund_name_validation(value: Any) -> None:
    with pytest.raises(InvalidValueError, match="fund_name"):
        PvdFacts(fund_name=value)


def test_c02a_fact_flags_must_not_coerce_strings() -> None:
    for model, field in [
        (PvdFacts, "registered_fund"),
        (OtherRightsFacts, "rmf"),
        (FundHistoryFacts, "prior_conditional_rights"),
    ]:
        with pytest.raises(InvalidValueError, match="boolean"):
            model(**{field: "false"})
    fact = PvdFacts(employee_paid=Money.zero())
    result = facts_to_dict(fact)
    assert result is not None
    assert result["employee_paid"] == "0.00"
    with pytest.raises(FrozenInstanceError):
        fact.employee_paid = Money.of(1)  # type: ignore[misc]
    assert facts_to_dict(None) is None
    assert replace(fact, registered_fund=False).registered_fund is False
