"""C02A-AC08: HEAD content pins, portable across Git CRLF/LF checkouts."""

import hashlib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("path", "digest"),
    [
        (
            "src/tax_gps/policy/packs/TH-PIT-2026-001.json",
            "593ada7f90289adeb941599bf043f25f9d5dad1e4f87a8e95c371fc2b1ef839f",
        ),
        (
            "src/tax_gps/policy/packs/TH-PIT-2026-001@1.0.1.json",
            "8eb3a98f153fba7d01d15e27fbb1e2a2bbb1b8b5197a557aac7b81307e75f4af",
        ),
        (
            "src/tax_gps/opportunity/catalogs/TH-OPPORTUNITY-2026-001.json",
            "1c2bc2d38e682eea6412f825096a407b980415fbafd8d9d9223b10993cee814d",
        ),
        (
            "src/tax_gps/opportunity/catalogs/TH-OPPORTUNITY-2026-001@1.0.1.json",
            "5831327f5cb67d1dd7682a66011211944f9b9abbc35fd516a7be7f8a82440f55",
        ),
        (
            "src/tax_gps/policy/packs/TH-PIT-2026-001@1.1.0.json",
            "cb61b0e3fe53f7960de942f4d44a09cc144063125cc204fac7068704f73dded1",
        ),
        (
            "src/tax_gps/opportunity/catalogs/TH-OPPORTUNITY-2026-001@1.1.0.json",
            "b30009a713326e8147b9fcb5ad01dcfebaed743cf1c6240159982eb1b63cc2c5",
        ),
    ],
)
def test_c02a_released_artifact_bytes_remain_unchanged(path: str, digest: str) -> None:
    assert hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest
