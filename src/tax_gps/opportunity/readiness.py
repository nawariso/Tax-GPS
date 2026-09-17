"""Per-opportunity policy verification gate."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from tax_gps.opportunity.models import OpportunityCatalog, OpportunityDefinition, OpportunityRule
from tax_gps.policy.activation import ActivatedRulePack
from tax_gps.policy.models import RuleSource, RuleStatus, SourceAuthority, TaxRule
from tax_gps.policy.readiness import ReadinessCode, ReadinessFinding


@dataclass(frozen=True, slots=True)
class OpportunityReadiness:
    findings: tuple[ReadinessFinding, ...]

    @property
    def ready(self) -> bool:
        return not self.findings


def _authoritative(source: RuleSource) -> bool:
    parsed = urlsplit(source.url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if source.authority is SourceAuthority.OFFICIAL_PROVIDER:
        return True
    return parsed.hostname == "go.th" or parsed.hostname.endswith(".go.th")


def _finding(code: ReadinessCode, subject: str, message: str) -> ReadinessFinding:
    return ReadinessFinding(code, subject, message)


def _resolve_source(
    source_id: str, catalog: OpportunityCatalog, pack: ActivatedRulePack
) -> RuleSource | None:
    return catalog.find_source(source_id) or pack.pack.find_source(source_id)


def _check_rule(
    rule: OpportunityRule | TaxRule,
    catalog: OpportunityCatalog,
    pack: ActivatedRulePack,
    findings: list[ReadinessFinding],
) -> None:
    if rule.status is not RuleStatus.EFFECTIVE:
        findings.append(
            _finding(ReadinessCode.RULE_NOT_EFFECTIVE, rule.rule_id, "rule is not EFFECTIVE")
        )
    if rule.verified_at is None:
        findings.append(
            _finding(ReadinessCode.RULE_NOT_VERIFIED, rule.rule_id, "rule is not verified")
        )
    if rule.tax_year != pack.pack.tax_year:
        findings.append(
            _finding(
                ReadinessCode.RULE_TAX_YEAR_MISMATCH,
                rule.rule_id,
                "rule tax year differs from pack",
            )
        )
    if rule.source_id is None or not rule.source_id.strip():
        findings.append(
            _finding(ReadinessCode.RULE_SOURCE_MISSING, rule.rule_id, "rule source is missing")
        )
    else:
        source = _resolve_source(rule.source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    rule.rule_id,
                    "rule source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    rule.rule_id,
                    "rule source is not authoritative HTTPS",
                )
            )
    for source_id in rule.supplementary_source_ids:
        source = _resolve_source(source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    rule.rule_id,
                    "supplementary source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    rule.rule_id,
                    "supplementary source is not authoritative HTTPS",
                )
            )


def evaluate_opportunity_readiness(
    definition: OpportunityDefinition,
    catalog: OpportunityCatalog,
    pack: ActivatedRulePack,
) -> OpportunityReadiness:
    findings: list[ReadinessFinding] = []
    for rule_id in definition.rule_ids:
        rule = catalog.find_rule(rule_id) or pack.pack.find_rule(rule_id)
        if rule is None:
            findings.append(
                _finding(ReadinessCode.REQUIRED_RULE_MISSING, rule_id, "required rule is missing")
            )
        else:
            _check_rule(rule, catalog, pack, findings)
    for source_id in definition.source_ids:
        source = _resolve_source(source_id, catalog, pack)
        if source is None:
            findings.append(
                _finding(
                    ReadinessCode.RULE_SOURCE_UNRESOLVED,
                    definition.opportunity_id,
                    "declared source does not resolve",
                )
            )
        elif not _authoritative(source):
            findings.append(
                _finding(
                    ReadinessCode.SOURCE_NOT_AUTHORITATIVE,
                    definition.opportunity_id,
                    "declared source is not authoritative HTTPS",
                )
            )
    return OpportunityReadiness(tuple(findings))
