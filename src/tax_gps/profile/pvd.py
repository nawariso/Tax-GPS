"""Explicit immutable C02A facts; absent answers never authorize a deduction."""

from dataclasses import dataclass, fields

from tax_gps.core.errors import InvalidValueError
from tax_gps.core.money import Money


class PvdWageBasisError(InvalidValueError):
    """Code-owned field failure, independent of the presentation adapter."""

    def __init__(self) -> None:
        super().__init__("pvd.wage_basis conflicts with employment income")


def _booleans(value: "OtherRightsFacts | FundHistoryFacts") -> None:
    for item in fields(value):
        answer = getattr(value, item.name)
        if answer is not None and not isinstance(answer, bool):
            raise InvalidValueError(f"{item.name} must be boolean or null")


@dataclass(frozen=True, slots=True)
class PvdFacts:
    employee_paid: Money | None = None
    wage_basis: Money | None = None
    fund_name: str | None = None
    registered_fund: bool | None = None
    credited_in_tax_year: bool | None = None
    single_employer: bool | None = None
    single_fund: bool | None = None
    ordinary_article_rate: bool | None = None
    normal_remittance: bool | None = None

    def __post_init__(self) -> None:
        for name in ("employee_paid", "wage_basis"):
            amount = getattr(self, name)
            if amount is not None and (not isinstance(amount, Money) or amount.is_negative()):
                raise InvalidValueError(f"pvd.{name} must be nonnegative money or null")
        if self.fund_name is not None and (
            not isinstance(self.fund_name, str) or not self.fund_name.strip()
        ):
            raise InvalidValueError("pvd.fund_name must be named or null")
        for item in fields(self):
            if item.name not in ("employee_paid", "wage_basis", "fund_name"):
                value = getattr(self, item.name)
                if value is not None and not isinstance(value, bool):
                    raise InvalidValueError(f"pvd.{item.name} must be boolean or null")


@dataclass(frozen=True, slots=True)
class OtherRightsFacts:
    rmf: bool | None = None
    thai_esg: bool | None = None
    thai_esgx: bool | None = None
    gpf: bool | None = None
    teacher_fund: bool | None = None
    nsf: bool | None = None
    pension_insurance: bool | None = None
    ssf: bool | None = None
    spouse_pvd_claim: bool | None = None
    other_retirement_right: bool | None = None

    def __post_init__(self) -> None:
        _booleans(self)


@dataclass(frozen=True, slots=True)
class FundHistoryFacts:
    prior_conditional_rights: bool | None = None
    disposal_withdrawal_transfer: bool | None = None
    retirement_or_recapture: bool | None = None
    ltf_carryforward: bool | None = None

    def __post_init__(self) -> None:
        _booleans(self)


def facts_to_dict(
    value: PvdFacts | OtherRightsFacts | FundHistoryFacts | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        item.name: answer.canonical()
        if isinstance(answer := getattr(value, item.name), Money)
        else answer
        for item in fields(value)
    }
