"""Unit tests for canonical serialization and SHA-256 hashing (TGPS-P1-001 §9)."""

from decimal import Decimal
from types import MappingProxyType

import pytest

from tax_gps.core.canonical import (
    CanonicalizationError,
    canonical_json,
    freeze,
    sha256_hex,
    thaw,
)


def test_keys_are_sorted_and_whitespace_free() -> None:
    assert canonical_json({"b": 1, "a": [True, None, "x"]}) == b'{"a":[true,null,"x"],"b":1}'


def test_key_order_does_not_change_output() -> None:
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_non_ascii_is_utf8_not_escaped() -> None:
    assert canonical_json({"th": "ภาษี"}) == '{"th":"ภาษี"}'.encode()


def test_tuples_and_mapping_proxies_are_supported() -> None:
    frozen = MappingProxyType({"a": (1, 2)})
    assert canonical_json(frozen) == b'{"a":[1,2]}'


@pytest.mark.negative
@pytest.mark.parametrize("value", [1.5, Decimal("1.5"), {1: "x"}, object(), {"a": {1, 2}}])
def test_non_canonical_values_are_rejected(value: object) -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json(value)


def test_sha256_hex_known_vector() -> None:
    assert sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_freeze_is_deeply_immutable_and_thaw_round_trips() -> None:
    data = {"a": [1, {"b": ["c"]}], "d": None}
    frozen = freeze(data)
    assert isinstance(frozen, MappingProxyType)
    inner = frozen["a"]
    assert isinstance(inner, tuple)
    with pytest.raises(TypeError):
        frozen["a"] = 1  # type: ignore[index]
    assert thaw(frozen) == data


def test_freeze_rejects_unsupported_values() -> None:
    with pytest.raises(CanonicalizationError):
        freeze({"a": 1.0})
