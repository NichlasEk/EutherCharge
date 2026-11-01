#!/usr/bin/env python3
"""Prepare a title-pointer probe to the existing maximum-size string record."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


IMAGE_SIZE = 4 * 1024 * 1024
INSTALLED_SHA256 = "4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329"
POINTER_BASE = 0x003200
POINTER_OFFSET = 0x003604
SOURCE_RELATIVE = 0x00000692
TARGET_RELATIVE = 0x00004CC2
TARGET_RECORD = POINTER_BASE + TARGET_RELATIVE
TARGET_ALLOCATION = 113
TARGET_RECORD_SHA256 = "a5a5f3fffc708581f0b63149ad3c714fd6d36ac0e275b31d18d6def60a309a79"
TARGET_PAYLOAD_SHA256 = "14c5ceffc1c854db65a1bb2d30f5a9bf57f9a2b347ded1e9dd900a747ffded26"
SECTOR_BASE = 0x003000
SECTOR_SIZE = 0x1000
ORIGINAL_CRC32B = 0xF5C23372
PATCHED_CRC32B = 0xDE37C157


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def prepare(image: bytes) -> tuple[bytes, bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"image is {len(image)} bytes, expected {IMAGE_SIZE}")
    digest = sha256(image)
    if digest != INSTALLED_SHA256:
        raise ValueError(f"refusing unknown base image SHA-256 {digest}")
    pointer = struct.unpack_from(">I", image, POINTER_OFFSET)[0]
    if pointer != SOURCE_RELATIVE:
        raise ValueError(f"title pointer is 0x{pointer:08x}, expected 0x{SOURCE_RELATIVE:08x}")
    allocation = struct.unpack_from(">H", image, TARGET_RECORD)[0]
    record = image[TARGET_RECORD : TARGET_RECORD + 2 + allocation]
    payload = record[2:]
    if allocation != TARGET_ALLOCATION:
        raise ValueError(f"target allocation is {allocation}, expected {TARGET_ALLOCATION}")
    if sha256(record) != TARGET_RECORD_SHA256 or sha256(payload) != TARGET_PAYLOAD_SHA256:
        raise ValueError("maximum-record payload precondition failed")
    if payload[-1] != 0:
        raise ValueError("maximum record is not NUL-terminated")

    original = image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE]
    if crc32b(original) != ORIGINAL_CRC32B:
        raise ValueError("original sector CRC precondition failed")
    patched_image = bytearray(image)
    struct.pack_into(">I", patched_image, POINTER_OFFSET, TARGET_RELATIVE)
    changed = [index for index, pair in enumerate(zip(image, patched_image)) if pair[0] != pair[1]]
    expected_changes = [POINTER_OFFSET + 2, POINTER_OFFSET + 3]
    if changed != expected_changes:
        raise AssertionError(f"unexpected changed offsets: {changed}")
    patched = bytes(patched_image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(patched) != PATCHED_CRC32B:
        raise AssertionError("patched sector CRC no longer matches fixed helper")

    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-existing-maximum-record-title-pointer",
        "source": {"size_bytes": len(image), "sha256": digest},
        "target": {
            "bank": "Russian-custom",
            "entry_index_zero_based": 110,
            "entry_number_one_based": 111,
            "pointer_offset": f"0x{POINTER_OFFSET:06x}",
            "pointer_before": f"0x{SOURCE_RELATIVE:08x}",
            "pointer_after": f"0x{TARGET_RELATIVE:08x}",
            "record_offset": f"0x{TARGET_RECORD:06x}",
            "allocation": allocation,
            "visible_payload_bytes": allocation - 1,
            "record_sha256": sha256(record),
            "payload_sha256": sha256(payload),
            "changed_offsets": [f"0x{value:06x}" for value in expected_changes],
        },
        "hashes": {
            "original_sector_crc32b": f"{crc32b(original):08x}",
            "original_sector_sha256": sha256(original),
            "patched_sector_crc32b": f"{crc32b(patched):08x}",
            "patched_sector_sha256": sha256(patched),
            "patched_full_image_sha256": sha256(bytes(patched_image)),
        },
        "invariants": {
            "only_two_pointer_bytes_differ": True,
            "target_is_existing_valid_record": True,
            "payload_modified": False,
            "length_modified": False,
            "allocation_is_verified_format_maximum": True,
            "source_image_modified": False,
        },
        "safety": {
            "write_not_authorized_by_manifest": True,
            "requires_separate_crc_locked_restore": True,
            "capture_raw_sram_only_under_ignored_build_directory": True,
        },
    }
    return bytes(patched_image), original, patched, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    patched_image, original, patched, manifest = prepare(args.image.read_bytes())
    outputs = {
        "patched_image": args.output_dir / "maxrecord-full.bin",
        "original_sector": args.output_dir / "original-sector-003000.bin",
        "patched_sector": args.output_dir / "maxrecord-sector-003000.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    for prefix in ("original", "maxrecord"):
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"] = args.output_dir / f"{prefix}-sector-003000-chunk{index}.bin"
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patched_image"].write_bytes(patched_image)
    outputs["original_sector"].write_bytes(original)
    outputs["patched_sector"].write_bytes(patched)
    for prefix, sector in (("original", original), ("maxrecord", patched)):
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"].write_bytes(sector[index * 0x400 : (index + 1) * 0x400])
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
