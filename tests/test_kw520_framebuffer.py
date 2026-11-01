#!/usr/bin/env python3

import importlib.util
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "kw520_framebuffer", ROOT / "tools" / "kw520_framebuffer.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_page_major_lsb_coordinates() -> None:
    raw = bytearray(MODULE.FRAMEBUFFER_SIZE)
    raw[0] = 0b00000001
    raw[127] = 0b10000000
    raw[128] = 0b10000000
    rows = MODULE.decode_canvas(bytes(raw))
    assert rows[0][0] == 1
    assert rows[7][127] == 1
    assert rows[15][0] == 1
    assert rows[1][0] == 0
    assert rows[8][0] == 0


def test_png_dimensions_and_polarity() -> None:
    raw = bytes([1]) + bytes(MODULE.FRAMEBUFFER_SIZE - 1)
    canvas = MODULE.decode_canvas(raw)
    png = MODULE.encode_png(MODULE.visible_rows(canvas), scale=3)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (384, 192)


def test_visible_window_is_canvas_rows_24_through_87() -> None:
    raw = bytearray(MODULE.FRAMEBUFFER_SIZE)
    raw[3 * MODULE.WIDTH] = 1
    raw[2 * MODULE.WIDTH] = 1
    visible = MODULE.visible_rows(MODULE.decode_canvas(bytes(raw)))
    assert len(visible) == 64
    assert visible[0][0] == 1
    assert sum(sum(row) for row in visible) == 1
