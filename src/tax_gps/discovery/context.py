"""Explicit deterministic discovery context."""

from dataclasses import dataclass
from datetime import date

from tax_gps.core.tax_year import TaxYear


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    tax_year: TaxYear
    planning_date: date

    def to_dict(self) -> dict[str, object]:
        return {
            "tax_year": self.tax_year.gregorian,
            "planning_date": self.planning_date.isoformat(),
        }
