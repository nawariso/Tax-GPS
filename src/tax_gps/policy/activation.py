"""Production activation gate for structurally valid policy packs."""

from __future__ import annotations

from dataclasses import dataclass

from tax_gps.core.errors import TaxCoreError
from tax_gps.policy.loader import rule_pack_content_hash
from tax_gps.policy.models import RulePack
from tax_gps.policy.readiness import ReadinessFinding, evaluate_policy_readiness


class PolicyActivationError(TaxCoreError):
    def __init__(self, findings: tuple[ReadinessFinding, ...]) -> None:
        self.findings = findings
        message = "; ".join(f"{finding.code.value}: {finding.subject_id}" for finding in findings)
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ActivatedRulePack:
    pack: RulePack
    content_hash: str

    @property
    def rule_pack_id(self) -> str:
        return self.pack.rule_pack_id

    @property
    def version(self) -> str:
        return self.pack.version


def activate_rule_pack(pack: RulePack) -> ActivatedRulePack:
    readiness = evaluate_policy_readiness(pack)
    if not readiness.ready:
        raise PolicyActivationError(readiness.findings)
    return ActivatedRulePack(pack, rule_pack_content_hash(pack))
