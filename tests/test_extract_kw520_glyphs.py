#!/usr/bin/env python3

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "extract_kw520_glyphs", ROOT / "tools" / "extract_kw520_glyphs.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_cell_column_round_trip() -> None:
    columns = bytes.fromhex("010204081020")
    rows = MODULE.unpack_cell(columns)
    assert MODULE.extract_cell(rows, 0, 0, False) == columns


def test_inverted_cell_extraction() -> None:
    columns = bytes.fromhex("7e424242427e")
    normal = MODULE.unpack_cell(columns)
    inverted = [[pixel ^ 1 for pixel in row] for row in normal]
    assert MODULE.extract_cell(inverted, 0, 0, True) == columns


def test_title_and_numbered_rows_have_distinct_origins() -> None:
    page1 = MODULE.PROFILES["page1"]
    page2 = MODULE.PROFILES["page2"]
    assert page1[0][1] == 32
    assert page2[0][1] == 32
    assert all(definition[1] == 28 for definition in page1[1:])
    assert page2[1][1] == 28
