#!/usr/bin/env python3

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "combine_kw520_glyphs", ROOT / "tools" / "combine_kw520_glyphs.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def manifests() -> list[dict[str, object]]:
    glyphs = [
        {"code": f"0x{code:02x}", "columns_lsb_top_hex": (bytes([code]) * 6).hex()}
        for code in range(0x80, 0x100)
    ]
    return [{"glyphs": glyphs[:32]}, {"glyphs": glyphs[32:64]}, {"glyphs": glyphs[64:]}]


def test_complete_table_is_ordered() -> None:
    raw, atlas = MODULE.combine(manifests())
    assert len(raw) == 128 * 6
    assert raw[:6] == bytes([0x80]) * 6
    assert raw[-6:] == bytes([0xFF]) * 6
    assert len(atlas) == 64


def test_duplicate_is_refused() -> None:
    data = manifests()
    data[1]["glyphs"].append(data[0]["glyphs"][0])
    with pytest.raises(ValueError, match="duplicate glyph"):
        MODULE.combine(data)
