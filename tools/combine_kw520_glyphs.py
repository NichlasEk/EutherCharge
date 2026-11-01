#!/usr/bin/env python3
"""Combine exact KW520 glyph-capture manifests into one 0x80-0xff table."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "extract_kw520_glyphs", ROOT / "tools" / "extract_kw520_glyphs.py"
)
GLYPHS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GLYPHS)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def combine(manifests: list[dict[str, object]]) -> tuple[bytes, list[list[int]]]:
    cells: dict[int, bytes] = {}
    for manifest in manifests:
        for glyph in manifest["glyphs"]:
            code = int(glyph["code"], 16)
            columns = bytes.fromhex(glyph["columns_lsb_top_hex"])
            if code in cells:
                raise ValueError(f"duplicate glyph 0x{code:02x}")
            if len(columns) != GLYPHS.CELL_WIDTH:
                raise ValueError(f"glyph 0x{code:02x} is not six bytes")
            cells[code] = columns
    expected = set(range(0x80, 0x100))
    missing = sorted(expected - cells.keys())
    unexpected = sorted(cells.keys() - expected)
    if missing or unexpected:
        raise ValueError(
            "glyph coverage mismatch: "
            f"missing={[f'0x{x:02x}' for x in missing]} "
            f"unexpected={[f'0x{x:02x}' for x in unexpected]}"
        )

    raw = b"".join(cells[code] for code in range(0x80, 0x100))
    atlas = [[0] * GLYPHS.FB.WIDTH for _ in range(GLYPHS.FB.VISIBLE_HEIGHT)]
    for offset, code in enumerate(range(0x80, 0x100)):
        glyph_rows = GLYPHS.unpack_cell(cells[code])
        row = offset // 16
        column = offset % 16
        for y in range(GLYPHS.CELL_HEIGHT):
            for x in range(GLYPHS.CELL_WIDTH):
                atlas[row * GLYPHS.CELL_HEIGHT + y][column * GLYPHS.CELL_WIDTH + x] = glyph_rows[y][x]
    return raw, atlas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", type=Path, nargs=3)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source_bytes = [path.read_bytes() for path in args.manifests]
    manifests = [json.loads(data) for data in source_bytes]
    raw, atlas = combine(manifests)
    atlas_png = GLYPHS.FB.encode_png(atlas, scale=4)
    outputs = {
        "raw": args.output_dir / "kw520-glyphs-80-ff-6x8.bin",
        "png": args.output_dir / "kw520-glyphs-80-ff-6x8.png",
        "json": args.output_dir / "kw520-glyphs-80-ff-6x8.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["raw"].write_bytes(raw)
    outputs["png"].write_bytes(atlas_png)
    report = {
        "format": 1,
        "operation": "kw520-complete-exact-high-glyph-table",
        "range": "0x80-0xff",
        "glyph_count": 128,
        "glyph_format": "6 column bytes per glyph, bit 0 is top pixel",
        "sources": [
            {"path": str(path), "sha256": sha256(data)}
            for path, data in zip(args.manifests, source_bytes)
        ],
        "binary": {
            "path": str(outputs["raw"]),
            "size_bytes": len(raw),
            "sha256": sha256(raw),
        },
        "atlas_png": {
            "path": str(outputs["png"]),
            "sha256": sha256(atlas_png),
        },
        "verification": "every code 0x80-0xff occurred exactly once and every glyph was exactly six bytes",
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    outputs["json"].write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
