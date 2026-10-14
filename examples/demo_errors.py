"""Public, structured demo errors; never include submitted financial amounts."""


class DemoInputError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "INPUT_REQUIRED",
        status: str = "REQUIRES_INPUT",
        reason_codes: tuple[str, ...] = (),
        missing_fact_ids: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.reason_codes = reason_codes
        self.missing_fact_ids = missing_fact_ids

    def to_dict(self) -> dict[str, object]:
        return {
            "error": str(self),
            "code": self.code,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "missing_fact_ids": list(self.missing_fact_ids),
        }
