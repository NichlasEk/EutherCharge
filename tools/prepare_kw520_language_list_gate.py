#!/usr/bin/env python3
"""Prepare a consistent ninth language in both KW520 ID list and directory."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools" / "prepare_kw520_language_gate.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_language_gate_base", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BASE)

LIST_COUNT_OFFSET = 0x3041
SELECTED_ID_OFFSET = 0x3042
ID_LIST_OFFSET = 0x3043
ORIGINAL_IDS = bytes((3, 4, 5, 6, 7, 8, 10, 14))
PROBE_IDS = bytes((3, 4, 5, 6, 7, 8, 9, 10, 14))
EXPECTED_PROBE_CRC32 = 0x4779B7F4
EXPECTED_PROBE_SHA256 = "3fc0b1c28a4902a4a486d558dc6f764d6aa179bd4cb487383074990444818404"


def prepare(image: bytes) -> tuple[bytes, bytes, dict[str, object]]:
    original, directory_probe, base_manifest = BASE.prepare(image)
    relative_count = LIST_COUNT_OFFSET - BASE.SECTOR_START
    relative_selected = SELECTED_ID_OFFSET - BASE.SECTOR_START
    relative_ids = ID_LIST_OFFSET - BASE.SECTOR_START
    if original[relative_count] != 8:
        raise ValueError("refusing unexpected language-list count")
    if original[relative_selected] != 3:
        raise ValueError("refusing unexpected selected language ID")
    if original[relative_ids:relative_ids + len(ORIGINAL_IDS)] != ORIGINAL_IDS:
        raise ValueError("refusing unexpected active language ID list")
    if original[relative_ids + len(ORIGINAL_IDS)] != 0:
        raise ValueError("refusing nonzero insertion byte after language ID list")

    probe = bytearray(directory_probe)
    probe[relative_count] = len(PROBE_IDS)
    probe[relative_ids:relative_ids + len(PROBE_IDS)] = PROBE_IDS
    probe = bytes(probe)
    if BASE.crc32(probe) != EXPECTED_PROBE_CRC32:
        raise AssertionError("derived listed-language probe CRC32 changed")
    if BASE.sha256(probe) != EXPECTED_PROBE_SHA256:
        raise AssertionError("derived listed-language probe SHA-256 changed")

    changed = [
        {"absolute_offset": f"0x{BASE.SECTOR_START + index:06x}", "before": before, "after": after}
        for index, (before, after) in enumerate(zip(original, probe))
        if before != after
    ]
    manifest: dict[str, object] = {
        "purpose": "consistent ninth-language list plus descriptor SRAM-mapping gate",
        "source_image": base_manifest["source_image"],
        "sector": {
            "address": f"0x{BASE.SECTOR_START:06x}",
            "size": BASE.SECTOR_SIZE,
            "original_crc32": f"{BASE.crc32(original):08x}",
            "probe_crc32": f"{BASE.crc32(probe):08x}",
            "original_sha256": BASE.sha256(original),
            "probe_sha256": BASE.sha256(probe),
        },
        "language_list": {
            "count_offset": f"0x{LIST_COUNT_OFFSET:06x}",
            "selected_id_offset": f"0x{SELECTED_ID_OFFSET:06x}",
            "id_list_offset": f"0x{ID_LIST_OFFSET:06x}",
            "selected_id_unchanged": 3,
            "ids_before": list(ORIGINAL_IDS),
            "ids_after": list(PROBE_IDS),
        },
        "directory": base_manifest["directory"],
        "changed_bytes": changed,
        "observation": [
            "cold-start and verify ninth language is visible",
            "capture the same 16 KiB SRAM window used by the qualified baseline",
            "restore the exact original sector before further interpretation",
        ],
    }
    return original, probe, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    args.output.mkdir(parents=True, exist_ok=True)
    original, probe, manifest = prepare(args.image.read_bytes())
    (args.output / "original-sector-003000.bin").write_bytes(original)
    (args.output / "language9-listed-test-sector-003000.bin").write_bytes(probe)
    BASE.write_chunks(args.output, "original-sector-003000", original)
    BASE.write_chunks(args.output, "language9-listed-test-sector-003000", probe)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
