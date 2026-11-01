#!/usr/bin/env python3
"""Prepare a two-stage bounded declared-length extension in unused padding."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


IMAGE_SIZE = 4 * 1024 * 1024
INSTALLED_SHA256 = "4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329"
SECTOR_BASE = 0x003000
SECTOR_SIZE = 0x1000
POINTER_BASE = 0x003200
TITLE_POINTER_OFFSET = 0x003604
TITLE_POINTER_BEFORE = 0x00000692
NESTED_RECORD = 0x003DC7
NESTED_RELATIVE = NESTED_RECORD - POINTER_BASE
NESTED_ORIGINAL = bytes(10)
BASELINE_RECORD = b"\x00\x04SAFEWXYZ"
EXTENDED_RECORD = b"\x00\x08SAFEWXYZ"
ORIGINAL_CRC32B = 0xF5C23372
BASELINE_CRC32B = 0xB461D992
EXTENDED_CRC32B = 0xE4E92A7B


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def prepare(image: bytes) -> tuple[bytes, bytes, bytes, bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"image is {len(image)} bytes, expected {IMAGE_SIZE}")
    digest = sha256(image)
    if digest != INSTALLED_SHA256:
        raise ValueError(f"refusing unknown base image SHA-256 {digest}")
    if struct.unpack_from(">I", image, TITLE_POINTER_OFFSET)[0] != TITLE_POINTER_BEFORE:
        raise ValueError("main-title pointer precondition failed")
    if image[NESTED_RECORD : NESTED_RECORD + 10] != NESTED_ORIGINAL:
        raise ValueError("selected padding is not the expected ten zero bytes")
    original = image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE]
    if crc32b(original) != ORIGINAL_CRC32B:
        raise ValueError("original sector CRC precondition failed")

    baseline_image = bytearray(image)
    struct.pack_into(">I", baseline_image, TITLE_POINTER_OFFSET, NESTED_RELATIVE)
    baseline_image[NESTED_RECORD : NESTED_RECORD + 10] = BASELINE_RECORD
    baseline = bytes(baseline_image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(baseline) != BASELINE_CRC32B:
        raise AssertionError("baseline CRC no longer matches fixed helper")

    extended_image = bytearray(baseline_image)
    extended_image[NESTED_RECORD + 1] = 8
    extended = bytes(extended_image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(extended) != EXTENDED_CRC32B:
        raise AssertionError("extended CRC no longer matches fixed helper")

    extension_changes = [
        index for index, (old, new) in enumerate(zip(baseline_image, extended_image))
        if old != new
    ]
    if extension_changes != [NESTED_RECORD + 1]:
        raise AssertionError(f"unexpected extension changes: {extension_changes}")

    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-bounded-nested-record-length-extension",
        "source": {"size_bytes": len(image), "sha256": digest},
        "layout": {
            "title_pointer_offset": f"0x{TITLE_POINTER_OFFSET:06x}",
            "title_pointer_before": f"0x{TITLE_POINTER_BEFORE:08x}",
            "title_pointer_after": f"0x{NESTED_RELATIVE:08x}",
            "nested_record_offset": f"0x{NESTED_RECORD:06x}",
            "location": "ten bytes of verified zero padding inside entry 98 allocation",
            "baseline_record_hex": BASELINE_RECORD.hex(),
            "extended_record_hex": EXTENDED_RECORD.hex(),
            "baseline_length": 4,
            "extended_length": 8,
            "payload": "SAFEWXYZ",
            "extension_changed_offset": f"0x{NESTED_RECORD + 1:06x}",
        },
        "hashes": {
            "original_sector_crc32b": f"{crc32b(original):08x}",
            "original_sector_sha256": sha256(original),
            "baseline_sector_crc32b": f"{crc32b(baseline):08x}",
            "baseline_sector_sha256": sha256(baseline),
            "extended_sector_crc32b": f"{crc32b(extended):08x}",
            "extended_sector_sha256": sha256(extended),
        },
        "expected_observations": {
            "baseline": "SAFE",
            "extended": "SAFEWXYZ",
        },
        "safety": {
            "active_neighbor_record_modified": False,
            "maximum_test_length": 8,
            "known_valid_resource_maximum": 113,
            "single_sector_only": True,
            "power_or_calibration_data_modified": False,
            "write_not_authorized_by_manifest": True,
        },
    }
    return bytes(baseline_image), bytes(extended_image), original, baseline, extended, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    baseline_image, extended_image, original, baseline, extended, manifest = prepare(args.image.read_bytes())
    outputs = {
        "original_sector": args.output_dir / "original-sector-003000.bin",
        "baseline_sector": args.output_dir / "baseline-sector-003000.bin",
        "extended_sector": args.output_dir / "extended-sector-003000.bin",
        "baseline_image": args.output_dir / "baseline-full.bin",
        "extended_image": args.output_dir / "extended-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    for prefix in ("original", "baseline", "extended"):
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"] = args.output_dir / f"{prefix}-sector-003000-chunk{index}.bin"
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["original_sector"].write_bytes(original)
    outputs["baseline_sector"].write_bytes(baseline)
    outputs["extended_sector"].write_bytes(extended)
    outputs["baseline_image"].write_bytes(baseline_image)
    outputs["extended_image"].write_bytes(extended_image)
    for prefix, sector in (("original", original), ("baseline", baseline), ("extended", extended)):
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"].write_bytes(sector[index * 0x400 : (index + 1) * 0x400])
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
