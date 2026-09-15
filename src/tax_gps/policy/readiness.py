"""Policy Readiness decision kept separate for eventual DMN mapping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from urllib.parse import urlsplit

from tax_gps.policy import rule_ids
from tax_gps.policy.models import RulePack, RuleSource, RuleStatus, SourceAuthority

REQUIRED_RULE_IDS = rule_ids.ALL_RULE_IDS
_GOVERNMENT_SUFFIXES = (".go.th",)


class ReadinessCode(StrEnum):
    PACK_NOT_EFFECTIVE = "PACK_NOT_EFFECTIVE"
    RULE_NOT_EFFECTIVE = "RULE_NOT_EFFECTIVE"
    RULE_SOURCE_MISSING = "RULE_SOURCE_MISSING"
    RULE_SOURCE_UNRESOLVED = "RULE_SOURCE_UNRESOLVED"
    SOURCE_NOT_AUTHORITATIVE = "SOURCE_NOT_AUTHORITATIVE"
    RULE_NOT_VERIFIED = "RULE_NOT_VERIFIED"
    REQUIRED_RULE_MISSING = "REQUIRED_RULE_MISSING"
    RULE_TAX_YEAR_MISMATCH = "RULE_TAX_YEAR_MISMATCH"
    RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR = "RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR"
    PACK_CURRENCY_UNSUPPORTED = "PACK_CURRENCY_UNSUPPORTED"
    PACK_JURISDICTION_UNSUPPORTED = "PACK_JURISDICTION_UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class ReadinessFinding:
    code: ReadinessCode
    subject_id: str
    message: str


@dataclass(frozen=True, slots=True)
class PolicyReadiness:
    findings: tuple[ReadinessFinding, ...]

    @property
    def ready(self) -> bool:
        return not self.findings


def _finding(code: ReadinessCode, subject: str, message: str) -> ReadinessFinding:
    return ReadinessFinding(code, subject, message)


def _authoritative_source(source: RuleSource) -> bool:
    parsed = urlsplit(source.url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if source.authority is SourceAuthority.OFFICIAL_PROVIDER:
        return True
    return any(
        parsed.hostname == suffix[1:] or parsed.hostname.endswith(suffix)
        for suffix in _GOVERNMENT_SUFFIXES
    )


def evaluate_policy_readiness(pack: RulePack) -> PolicyReadiness:  # noqa: PLR0912
    findings: list[ReadinessFinding] = []
    if pack.status is not RuleStatus.EFFECTIVE:
        findings.append(
            _finding(ReadinessCode.PACK_NOT_EFFECTIVE, pack.rule_pack_id, "pack is not EFFECTIVE")
        )
    if pack.currency != "THB":
        findings.append(
            _finding(
                ReadinessCode.PACK_CURRENCY_UNSUPPORTED, pack.rule_pack_id, "currency must be THB"
            )
        )
    if pack.jurisdiction != "TH":
        findings.append(
            _finding(
                ReadinessCode.PACK_JURISDICTION_UNSUPPORTED,
                pack.rule_pack_id,
                "jurisdiction must be TH",
            )
        )
    present = {rule.rule_id for rule in pack.rules}
    for required in REQUIRED_RULE_IDS:
        if required not in present:
            findings.append(
                _finding(ReadinessCode.REQUIRED_RULE_MISSING, required, "required rule is missing")
            )
    year_start = date(pack.tax_year.gregorian, 1, 1)
    year_end = date(pack.tax_year.gregorian, 12, 31)
    for rule in pack.rules:
        if rule.status is not RuleStatus.EFFECTIVE:
            findings.append(
                _finding(ReadinessCode.RULE_NOT_EFFECTIVE, rule.rule_id, "rule is not EFFECTIVE")
            )
        if rule.source_id is None or not rule.source_id.strip():
            findings.append(
                _finding(ReadinessCode.RULE_SOURCE_MISSING, rule.rule_id, "rule source is missing")
            )
        elif (source := pack.find_source(rule.source_id)) is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    rule.rule_id,
                    "rule source does not resolve",
                )
            )
        elif not _authoritative_source(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    rule.rule_id,
                    "rule source is not authoritative HTTPS",
                )
            )
        for source_id in rule.supplementary_source_ids:
            supplementary = pack.find_source(source_id)
            if supplementary is None:
                findings.append(
                    _finding(
                        ReadinessCode.RULE_SOURCE_UNRESOLVED,
                        rule.rule_id,
                        "supplementary source does not resolve",
                    )
                )
            elif not _authoritative_source(supplementary):
                findings.append(
                    _finding(
                        ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                        rule.rule_id,
                        "supplementary source is not authoritative HTTPS",
                    )
                )
        if rule.verified_at is None:
            findings.append(
                _finding(ReadinessCode.RULE_NOT_VERIFIED, rule.rule_id, "rule is not verified")
            )
        if rule.tax_year != pack.tax_year:
            findings.append(
                _finding(
                    ReadinessCode.RULE_TAX_YEAR_MISMATCH,
                    rule.rule_id,
                    "rule tax year differs from pack",
                )
            )
        if rule.effective_from > year_start or (
            rule.effective_to is not None and rule.effective_to < year_end
        ):
            findings.append(
                _finding(
                    ReadinessCode.RULE_PERIOD_DOES_NOT_COVER_TAX_YEAR,
                    rule.rule_id,
                    "rule period does not cover tax year",
                )
            )
    return PolicyReadiness(tuple(findings))
