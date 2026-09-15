"""Policy fixtures: the bundled production pack and helpers to derive mutated variants."""

import copy
import json
from functools import cache
from importlib.resources import files
from typing import Any

from tax_gps.policy.activation import ActivatedRulePack, activate_rule_pack
from tax_gps.policy.loader import BUNDLED_PACK_ID_2026, parse_rule_pack

PackDict = dict[str, Any]


@cache
def _bundled_text() -> str:
    resource = files("tax_gps.policy.packs").joinpath(f"{BUNDLED_PACK_ID_2026}.json")
    return resource.read_text(encoding="utf-8")


def bundled_pack_dict() -> PackDict:
    """A fresh, mutable copy of the bundled 2026 production pack."""
    data: PackDict = json.loads(_bundled_text())
    return copy.deepcopy(data)


def rule_dict(pack: PackDict, rule_id: str) -> dict[str, Any]:
    for rule in pack["rules"]:
        if rule["rule_id"] == rule_id:
            return rule  # type: ignore[no-any-return]
    raise KeyError(rule_id)


def source_dict(pack: PackDict, source_id: str) -> dict[str, Any]:
    for source in pack["sources"]:
        if source["source_id"] == source_id:
            return source  # type: ignore[no-any-return]
    raise KeyError(source_id)


def activate_dict(pack: PackDict) -> ActivatedRulePack:
    return activate_rule_pack(parse_rule_pack(json.dumps(pack)))


@cache
def production_pack() -> ActivatedRulePack:
    return activate_dict(bundled_pack_dict())
