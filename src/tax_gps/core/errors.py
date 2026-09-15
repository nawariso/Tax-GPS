"""Error hierarchy for the Tax GPS core.

Every error raised deliberately by the tax core derives from ``TaxCoreError`` so callers can
distinguish rejected inputs/policy from programming defects.
"""


class TaxCoreError(Exception):
    """Base class for all deliberate tax-core errors."""


class InvalidValueError(TaxCoreError, ValueError):
    """A value object received an invalid value."""


class InvalidMoneyError(InvalidValueError):
    """Invalid monetary amount."""


class InvalidPercentageError(InvalidValueError):
    """Invalid percentage / ratio."""


class InvalidTaxYearError(InvalidValueError):
    """Invalid tax year."""
