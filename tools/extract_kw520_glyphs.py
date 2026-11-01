#!/usr/bin/env python3
"""Extract exact 6x8 KW520 glyph cells from a controlled SRAM framebuffer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "kw520_framebuffer", ROOT / "tools" / "kw520_framebuffer.py"
)
FB = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FB)

CELL_WIDTH = 6
CELL_HEIGHT = 8
ROW_GLYPH_X = 28
TITLE_GLYPH_X = 32
PROFILES = {
    "page1": (
        (0x80, TITLE_GLYPH_X, 0, True),
        (0x90, ROW_GLYPH_X, 16, True),
        (0xB0, ROW_GLYPH_X, 40, False),
        (0xC0, ROW_GLYPH_X, 48, False),
    ),
    "page2": (
        (0xE0, TITLE_GLYPH_X, 0, True),
        (0xF0, ROW_GLYPH_X, 16, True),
    ),
    "missing": (
        (0xA0, ROW_GLYPH_X, 40, False),
        (0xD0, ROW_GLYPH_X, 48, False),
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_cell(
    rows: list[list[int]], x: int, y: int, inverted: bool
) -> bytes:
    if y < 0 or y + CELL_HEIGHT > len(rows) or x < 0 or x + CELL_WIDTH > len(rows[0]):
        raise ValueError("glyph cell exceeds framebuffer")
    columns = bytearray()
    for dx in range(CELL_WIDTH):
        value = 0
        for dy in range(CELL_HEIGHT):
            pixel = rows[y + dy][x + dx] ^ inverted
            value |= pixel << dy
        columns.append(value)
    return bytes(columns)


def unpack_cell(columns: bytes) -> list[list[int]]:
    if len(columns) != CELL_WIDTH:
        raise ValueError("glyph must contain six column bytes")
    return [
        [(columns[x] >> y) & 1 for x in range(CELL_WIDTH)]
        for y in range(CELL_HEIGHT)
    ]


def extract_profile(
    visible: list[list[int]], profile: str
) -> tuple[bytes, list[dict[str, object]], list[list[int]]]:
    definitions = PROFILES[profile]
    raw = bytearray()
    glyphs: list[dict[str, object]] = []
    atlas = [[0] * FB.WIDTH for _ in range(FB.VISIBLE_HEIGHT)]
    for group_row, (base, first_glyph_x, source_y, inverted) in enumerate(definitions):
        for index in range(16):
            code = base + index
            source_x = first_glyph_x + index * CELL_WIDTH
            columns = extract_cell(visible, source_x, source_y, inverted)
            reconstructed = unpack_cell(columns)
            for dy in range(CELL_HEIGHT):
                for dx in range(CELL_WIDTH):
                    expected = visible[source_y + dy][source_x + dx] ^ inverted
                    if reconstructed[dy][dx] != expected:
                        raise AssertionError(f"glyph 0x{code:02x} reconstruction mismatch")
                    atlas[group_row * CELL_HEIGHT + dy][index * CELL_WIDTH + dx] = reconstructed[dy][dx]
            raw.extend(columns)
            glyphs.append(
                {
                    "code": f"0x{code:02x}",
                    "columns_lsb_top_hex": columns.hex(),
                    "source_cell": {
                        "x": source_x,
                        "y": source_y,
                        "inverted": inverted,
                    },
                }
            )
    return bytes(raw), glyphs, atlas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="16 KiB SRAM capture")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.input.read_bytes()
    if len(source) != 0x4000:
        raise SystemExit(f"expected one 16 KiB SRAM capture, got {len(source)} bytes")
    framebuffer = source[: FB.FRAMEBUFFER_SIZE]
    visible = FB.visible_rows(FB.decode_canvas(framebuffer))
    raw, glyphs, atlas = extract_profile(visible, args.profile)
    atlas_png = FB.encode_png(atlas, scale=4)

    outputs = {
        "raw": args.output_dir / f"{args.profile}-glyphs-6x8.bin",
        "json": args.output_dir / f"{args.profile}-glyphs-6x8.json",
        "png": args.output_dir / f"{args.profile}-glyphs-6x8.png",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["raw"].write_bytes(raw)
    outputs["png"].write_bytes(atlas_png)
    manifest = {
        "format": 1,
        "operation": "kw520-exact-rendered-glyph-extraction",
        "profile": args.profile,
        "source": {
            "path": str(args.input),
            "size_bytes": len(source),
            "sha256": sha256(source),
        },
        "framebuffer": {
            "address": "0x20000000",
            "size_bytes": FB.FRAMEBUFFER_SIZE,
            "sha256": sha256(framebuffer),
            "visible_window": "128x64 canvas rows 24-87",
        },
        "glyph_format": "6 column bytes per glyph, bit 0 is top pixel",
        "glyph_count": len(glyphs),
        "raw": {
            "path": str(outputs["raw"]),
            "size_bytes": len(raw),
            "sha256": sha256(raw),
        },
        "atlas_png": {
            "path": str(outputs["png"]),
            "sha256": sha256(atlas_png),
        },
        "glyphs": glyphs,
        "verification": "every extracted six-byte glyph reconstructed its exact source cell",
    }
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    outputs["json"].write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
