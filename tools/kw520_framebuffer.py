#!/usr/bin/env python3
"""Decode the KW520 128x64 page-major LCD framebuffer from an SRAM dump."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


WIDTH = 128
CANVAS_HEIGHT = 128
VISIBLE_Y = 24
VISIBLE_HEIGHT = 64
PAGE_HEIGHT = 8
FRAMEBUFFER_SIZE = WIDTH * CANVAS_HEIGHT // 8
SRAM_BASE = 0x20000000
FRAMEBUFFER_ADDRESS = SRAM_BASE


def decode_canvas(raw: bytes) -> list[list[int]]:
    """Return the 128x128 backing canvas; one bits are dark LCD pixels."""

    if len(raw) != FRAMEBUFFER_SIZE:
        raise ValueError(
            f"expected exactly {FRAMEBUFFER_SIZE} framebuffer bytes, got {len(raw)}"
        )
    rows = [[0] * WIDTH for _ in range(CANVAS_HEIGHT)]
    for page in range(CANVAS_HEIGHT // PAGE_HEIGHT):
        for x in range(WIDTH):
            value = raw[page * WIDTH + x]
            for bit in range(PAGE_HEIGHT):
                rows[page * PAGE_HEIGHT + bit][x] = (value >> bit) & 1
    return rows


def visible_rows(canvas: list[list[int]]) -> list[list[int]]:
    if len(canvas) != CANVAS_HEIGHT or any(len(row) != WIDTH for row in canvas):
        raise ValueError("pixel matrix must be exactly 128x128")
    return canvas[VISIBLE_Y : VISIBLE_Y + VISIBLE_HEIGHT]


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def encode_png(rows: list[list[int]], scale: int = 1, invert: bool = False) -> bytes:
    if scale < 1 or scale > 32:
        raise ValueError("scale must be 1..32")
    height_pixels = len(rows)
    if height_pixels < 1 or any(len(row) != WIDTH for row in rows):
        raise ValueError("pixel matrix must have 128 columns")

    expanded = bytearray()
    for row in rows:
        scanline = bytearray()
        for pixel in row:
            dark = bool(pixel) ^ invert
            scanline.extend([0 if dark else 255] * scale)
        encoded = b"\x00" + bytes(scanline)
        for _ in range(scale):
            expanded.extend(encoded)

    width = WIDTH * scale
    height = height_pixels * scale
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        signature
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(expanded), 9))
        + png_chunk(b"IEND", b"")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="16 KiB SRAM dump or raw framebuffer")
    parser.add_argument("output", type=Path, help="output PNG")
    parser.add_argument("--offset", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument(
        "--canvas",
        action="store_true",
        help="render all 128 backing rows instead of the visible y=24..87 window",
    )
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}")
    source = args.input.read_bytes()
    end = args.offset + FRAMEBUFFER_SIZE
    if args.offset < 0 or end > len(source):
        raise SystemExit(
            f"framebuffer range 0x{args.offset:x}..0x{end:x} exceeds {len(source)} bytes"
        )
    framebuffer = source[args.offset:end]
    canvas = decode_canvas(framebuffer)
    rows = canvas if args.canvas else visible_rows(canvas)
    rendered = encode_png(rows, args.scale, args.invert)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered)
    print(
        json.dumps(
            {
                "input": str(args.input),
                "input_sha256": hashlib.sha256(source).hexdigest(),
                "framebuffer_address": f"0x{FRAMEBUFFER_ADDRESS + args.offset:08x}",
                "framebuffer_offset": args.offset,
                "framebuffer_sha256": hashlib.sha256(framebuffer).hexdigest(),
                "layout": "128x128 backing canvas, sixteen 128-byte pages, LSB-first vertical bits",
                "visible_window": "y=24..87" if not args.canvas else "full canvas",
                "output": str(args.output),
                "output_sha256": hashlib.sha256(rendered).hexdigest(),
                "scale": args.scale,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
