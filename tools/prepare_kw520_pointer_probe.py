#!/usr/bin/env python3
"""Prepare a fixed same-bank pointer-redirection probe for the KW520.

The probe changes only English/Swedish table entry 1, used as the main-menu
title, from the valid ``Huvudmeny`` record to the existing valid ``Testa``
record.  Neither record, allocation nor payload is modified.  Because the
pointer change requires NOR 0-to-1 transitions, the manifest explicitly
requires the qualified fixed-sector erase/program helper.
"""

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
TABLE_OFFSET = 0x003600
SOURCE_INDEX = 1
TARGET_INDEX = 2
POINTER_OFFSET = TABLE_OFFSET + SOURCE_INDEX * 4
SOURCE_RELATIVE = 0x00000692
TARGET_RELATIVE = 0x0000069E
SOURCE_RECORD = POINTER_BASE + SOURCE_RELATIVE
TARGET_RECORD = POINTER_BASE + TARGET_RELATIVE
SOURCE_PAYLOAD = b"Huvudmeny\0"
TARGET_PAYLOAD = b"Testa\0"
SECTOR_BASE = 0x003000
SECTOR_SIZE = 0x1000
ORIGINAL_SECTOR_CRC32B = 0xF5C23372
PATCHED_SECTOR_CRC32B = 0x14B0524B


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def read_record(image: bytes, offset: int) -> tuple[int, bytes]:
    allocation = struct.unpack_from(">H", image, offset)[0]
    payload = image[offset + 2 : offset + 2 + allocation]
    return allocation, payload


def prepare(image: bytes) -> tuple[bytes, bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"image is {len(image)} bytes, expected {IMAGE_SIZE}")
    digest = sha256(image)
    if digest != INSTALLED_SHA256:
        raise ValueError(
            "refusing an unknown base image: "
            f"SHA-256 {digest}, expected installed image {INSTALLED_SHA256}"
        )

    source_pointer = struct.unpack_from(">I", image, POINTER_OFFSET)[0]
    target_pointer = struct.unpack_from(">I", image, TABLE_OFFSET + TARGET_INDEX * 4)[0]
    if source_pointer != SOURCE_RELATIVE or target_pointer != TARGET_RELATIVE:
        raise ValueError(
            "pointer precondition failed: "
            f"source=0x{source_pointer:08x}, target=0x{target_pointer:08x}"
        )
    source_allocation, source_payload = read_record(image, SOURCE_RECORD)
    target_allocation, target_payload = read_record(image, TARGET_RECORD)
    if source_payload != SOURCE_PAYLOAD or target_payload != TARGET_PAYLOAD:
        raise ValueError(
            "record precondition failed: "
            f"source={source_payload!r}, target={target_payload!r}"
        )

    original_sector = image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE]
    if crc32b(original_sector) != ORIGINAL_SECTOR_CRC32B:
        raise ValueError("original sector CRC precondition failed")

    patched = bytearray(image)
    struct.pack_into(">I", patched, POINTER_OFFSET, TARGET_RELATIVE)
    changed = [index for index, (old, new) in enumerate(zip(image, patched)) if old != new]
    if changed != [POINTER_OFFSET + 3]:
        raise AssertionError(f"unexpected changed offsets: {changed}")

    patched_sector = bytes(patched[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(patched_sector) != PATCHED_SECTOR_CRC32B:
        raise AssertionError("patched sector CRC no longer matches the fixed helper")

    old_byte = image[POINTER_OFFSET + 3]
    new_byte = patched[POINTER_OFFSET + 3]
    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-same-bank-pointer-redirection",
        "source": {"size_bytes": len(image), "sha256": digest},
        "target": {
            "language_table": "English table carrying installed Swedish payloads",
            "table_offset": f"0x{TABLE_OFFSET:06x}",
            "source_index": SOURCE_INDEX,
            "pointer_offset": f"0x{POINTER_OFFSET:06x}",
            "pointer_before": f"0x{SOURCE_RELATIVE:08x}",
            "pointer_after": f"0x{TARGET_RELATIVE:08x}",
            "source_record": f"0x{SOURCE_RECORD:06x}",
            "target_record": f"0x{TARGET_RECORD:06x}",
            "source_allocation": source_allocation,
            "target_allocation": target_allocation,
            "source_text": "Huvudmeny",
            "target_text": "Testa",
            "changed_offsets": [f"0x{POINTER_OFFSET + 3:06x}"],
            "changed_byte": {"before": f"0x{old_byte:02x}", "after": f"0x{new_byte:02x}"},
            "contains_0_to_1_transition": (old_byte | new_byte) != old_byte,
            "sector_erase_required": True,
        },
        "hashes": {
            "original_sector_sha256": sha256(original_sector),
            "original_sector_crc32b": f"{crc32b(original_sector):08x}",
            "patched_sector_sha256": sha256(patched_sector),
            "patched_sector_crc32b": f"{crc32b(patched_sector):08x}",
            "patched_full_image_sha256": sha256(bytes(patched)),
        },
        "invariants": {
            "image_size_preserved": len(patched) == len(image),
            "only_one_pointer_byte_differs": True,
            "string_payload_bytes_modified": False,
            "length_prefixes_modified": False,
            "both_pointer_destinations_are_existing_valid_records": True,
        },
        "expected_observation": {
            "main_menu_title": "Testa",
            "meaning": "the original firmware followed table entry 1 to existing record 2",
        },
        "safety": {
            "source_image_modified": False,
            "write_not_authorized_by_manifest": True,
            "required_before_write": [
                "normal charger cold start",
                "live sector CRC equals f5c23372",
                "JEDEC ID equals 1c3016",
                "pointer-probe SRAM payload CRC equals 14b0524b",
                "fixed original-sector restoration helper remains available",
            ],
        },
    }
    return bytes(patched), original_sector, patched_sector, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    patched, original_sector, patched_sector, manifest = prepare(args.image.read_bytes())
    outputs = {
        "patched_sector": args.output_dir / "pointer-sector-003000.bin",
        "patch_chunk_0": args.output_dir / "pointer-sector-003000-chunk0.bin",
        "patch_chunk_1": args.output_dir / "pointer-sector-003000-chunk1.bin",
        "patch_chunk_2": args.output_dir / "pointer-sector-003000-chunk2.bin",
        "patch_chunk_3": args.output_dir / "pointer-sector-003000-chunk3.bin",
        "restore_sector": args.output_dir / "restore-sector-003000.bin",
        "restore_chunk_0": args.output_dir / "restore-sector-003000-chunk0.bin",
        "restore_chunk_1": args.output_dir / "restore-sector-003000-chunk1.bin",
        "restore_chunk_2": args.output_dir / "restore-sector-003000-chunk2.bin",
        "restore_chunk_3": args.output_dir / "restore-sector-003000-chunk3.bin",
        "patched_image": args.output_dir / "pointer-probe-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patched_sector"].write_bytes(patched_sector)
    for index in range(4):
        outputs[f"patch_chunk_{index}"].write_bytes(
            patched_sector[index * 0x400 : (index + 1) * 0x400]
        )
    outputs["restore_sector"].write_bytes(original_sector)
    for index in range(4):
        outputs[f"restore_chunk_{index}"].write_bytes(
            original_sector[index * 0x400 : (index + 1) * 0x400]
        )
    outputs["patched_image"].write_bytes(patched)
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    outputs["manifest"].write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
