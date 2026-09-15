"""Canonical JSON serialization and SHA-256 hashing.

Canonical form (defined before any hashing, TGPS-P1-001 §9):

* JSON (RFC 8259) encoded as UTF-8, non-ASCII characters emitted literally;
* object keys sorted lexicographically by code point; no insignificant whitespace;
* permitted values: ``str``, ``int``, ``bool``, ``None``, lists/tuples and string-keyed maps;
* numbers that are not integers (money, rates) MUST already be canonical decimal strings —
  floats and ``Decimal`` objects are rejected so no binary floating point can enter a hash.
"""

import hashlib
import json
from collections.abc import Mapping
from types import MappingProxyType

from tax_gps.core.errors import TaxCoreError

type JsonValue = (
    str
    | int
    | bool
    | tuple["JsonValue", ...]
    | list["JsonValue"]
    | Mapping[str, "JsonValue"]
    | None
)


class CanonicalizationError(TaxCoreError, TypeError):
    """A value cannot be represented in canonical form."""


def _check(value: object) -> None:
    if value is None or isinstance(value, str | bool | int):
        return
    if isinstance(value, list | tuple):
        for item in value:
            _check(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("canonical object keys must be strings")
            _check(item)
        return
    raise CanonicalizationError(f"value of type {type(value).__name__} is not canonical")


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    return value


def canonical_json(value: object) -> bytes:
    _check(value)
    text = json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def freeze(value: object) -> JsonValue:
    """Return a deeply immutable copy (maps -> MappingProxyType, lists -> tuple)."""
    _check(value)
    return _freeze(value)


def _freeze(value: object) -> JsonValue:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value  # type: ignore[return-value]


def thaw(value: JsonValue) -> object:
    """Return a mutable plain-JSON copy of a frozen value."""
    return _plain(value)
