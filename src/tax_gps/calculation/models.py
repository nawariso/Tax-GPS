"""Immutable calculation, explanation, and capacity models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from tax_gps.core.money import Money
from tax_gps.core.percentage import Percentage
from tax_gps.core.tax_year import TaxYear
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource


class TaxStatus(StrEnum):
    READY = "READY"
    UNSUPPORTED = "UNSUPPORTED"
    ADVANCED_TAX_PATH_REQUIRED = "ADVANCED_TAX_PATH_REQUIRED"


@dataclass(frozen=True, slots=True)
class CalculationStep:
    step_id: str
    description: str
    rule_id: str
    source_id: str
    input_amount: Money
    output_amount: Money
    rate: Percentage | None = None

    @property
    def amount(self) -> Money:
        """The calculated amount, for single-step rule results."""
        return self.output_amount

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "rule_id": self.rule_id,
            "source_id": self.source_id,
            "input_amount": self.input_amount.canonical(),
            "output_amount": self.output_amount.canonical(),
            "rate": self.rate.canonical() if self.rate is not None else None,
        }


@dataclass(frozen=True, slots=True)
class CalculationTrace:
    steps: tuple[CalculationStep, ...]

    def to_dict(self) -> list[dict[str, object]]:
        return [step.to_dict() for step in self.steps]


@dataclass(frozen=True, slots=True)
class IncomeCalculation:
    assessable_income: Money


@dataclass(frozen=True, slots=True)
class ExpenseCalculation:
    section_40_1: Money


@dataclass(frozen=True, slots=True)
class AllowanceCalculation:
    personal: Money
    social_security: Money
    parents: Money
    children: Money
    mortgage_interest: Money

    @property
    def total(self) -> Money:
        return Money.sum(
            (
                self.personal,
                self.social_security,
                self.parents,
                self.children,
                self.mortgage_interest,
            )
        )


@dataclass(frozen=True, slots=True)
class ExistingRight:
    category: str
    eligible: bool
    input_amount: Money
    deductible_amount: Money
    rule_id: str


@dataclass(frozen=True, slots=True)
class DeductionCapacity:
    category: str
    standalone_limit: Money
    amount_used: Money
    standalone_remaining: Money
    shared_group: str | None
    shared_limit: Money | None
    shared_amount_used: Money
    shared_remaining: Money | None
    usable_amount: Money


@dataclass(frozen=True, slots=True)
class ProgressivePitCalculation:
    tax: Money
    marginal_rate: Percentage
    steps: tuple[CalculationStep, ...]


@dataclass(frozen=True, slots=True)
class TaxImpact:
    taxable_before: Money
    taxable_after: Money
    pit_before: Money
    pit_after: Money
    saving: Money


@dataclass(frozen=True, slots=True)
class TaxState:
    status: TaxStatus
    tax_year: TaxYear
    income: IncomeCalculation
    expenses: ExpenseCalculation
    allowances: AllowanceCalculation
    taxable_income: Money | None
    pit: Money | None
    marginal_rate: Percentage | None
    existing_rights: tuple[ExistingRight, ...]
    deduction_capacities: tuple[DeductionCapacity, ...]
    calculation_trace: CalculationTrace
    rules_applied: tuple[str, ...]
    sources: tuple[RuleSource, ...]
    rule_pack: str
    rule_pack_version: str
    engine_version: str
    unsupported_reasons: tuple[str, ...]
    output_hash: str
    _activated_pack: ActivatedRulePack = field(repr=False, compare=False)

    def tax_impact(self, additional_deduction: Money) -> TaxImpact:
        if self.taxable_income is None:
            raise ValueError("tax impact is unavailable for unsupported tax state")
        from tax_gps.calculation.rules import calculate_tax_saving  # noqa: PLC0415

        return calculate_tax_saving(self.taxable_income, additional_deduction, self._activated_pack)

    def material_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "tax_year": self.tax_year.gregorian,
            "income": {"assessable_income": self.income.assessable_income.canonical()},
            "expenses": {"section_40_1": self.expenses.section_40_1.canonical()},
            "allowances": {
                "personal": self.allowances.personal.canonical(),
                "social_security": self.allowances.social_security.canonical(),
                "parents": self.allowances.parents.canonical(),
                "children": self.allowances.children.canonical(),
                "mortgage_interest": self.allowances.mortgage_interest.canonical(),
                "total": self.allowances.total.canonical(),
            },
            # Explicit `is not None`: a zero PIT is a real, material result and must serialize
            # as "0.00", never as null. Truthiness here would make a zero-tax taxpayer
            # indistinguishable from an unsupported calculation and would change the audit hash.
            "taxable_income": (
                self.taxable_income.canonical() if self.taxable_income is not None else None
            ),
            "pit": self.pit.canonical() if self.pit is not None else None,
            "marginal_rate": (
                self.marginal_rate.canonical() if self.marginal_rate is not None else None
            ),
            "existing_rights": [
                {
                    "category": right.category,
                    "eligible": right.eligible,
                    "input_amount": right.input_amount.canonical(),
                    "deductible_amount": right.deductible_amount.canonical(),
                    "rule_id": right.rule_id,
                }
                for right in self.existing_rights
            ],
            "deduction_capacities": [capacity_to_dict(item) for item in self.deduction_capacities],
            "calculation_trace": self.calculation_trace.to_dict(),
            "rules_applied": list(self.rules_applied),
            "sources": [
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "publisher": source.publisher,
                    "authority": source.authority.value,
                    "url": source.url,
                    "published_at": (
                        source.published_at.isoformat() if source.published_at else None
                    ),
                    "retrieved_at": source.retrieved_at.isoformat(),
                }
                for source in self.sources
            ],
            "rule_pack": self.rule_pack,
            "rule_pack_version": self.rule_pack_version,
            "engine_version": self.engine_version,
            "unsupported_reasons": list(self.unsupported_reasons),
        }

    def to_dict(self) -> dict[str, object]:
        result = self.material_dict()
        result["output_hash"] = self.output_hash
        return result


def capacity_to_dict(item: DeductionCapacity) -> dict[str, object]:
    return {
        "category": item.category,
        "standalone_limit": item.standalone_limit.canonical(),
        "amount_used": item.amount_used.canonical(),
        "standalone_remaining": item.standalone_remaining.canonical(),
        "shared_group": item.shared_group,
        "shared_limit": item.shared_limit.canonical() if item.shared_limit else None,
        "shared_amount_used": item.shared_amount_used.canonical(),
        "shared_remaining": item.shared_remaining.canonical() if item.shared_remaining else None,
        "usable_amount": item.usable_amount.canonical(),
    }
