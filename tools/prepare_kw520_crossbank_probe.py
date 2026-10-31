#!/usr/bin/env python3
"""Prepare a fixed valid pointer redirection into another KW520 language bank."""

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
SOURCE_TABLE = 0x003600
TARGET_TABLE = 0x004356
ENTRY_INDEX = 1
POINTER_OFFSET = SOURCE_TABLE + ENTRY_INDEX * 4
TARGET_POINTER_OFFSET = TARGET_TABLE + ENTRY_INDEX * 4
SOURCE_RELATIVE = 0x00000692
TARGET_RELATIVE = 0x000013E9
SOURCE_RECORD = POINTER_BASE + SOURCE_RELATIVE
TARGET_RECORD = POINTER_BASE + TARGET_RELATIVE
SOURCE_PAYLOAD = b"Huvudmeny\0"
TARGET_PAYLOAD = b"Menu principal\0"
SECTOR_BASE = 0x003000
SECTOR_SIZE = 0x1000
ORIGINAL_SECTOR_CRC32B = 0xF5C23372
PATCHED_SECTOR_CRC32B = 0xB29EE7D1


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def read_record(image: bytes, offset: int) -> tuple[int, bytes]:
    allocation = struct.unpack_from(">H", image, offset)[0]
    return allocation, image[offset + 2 : offset + 2 + allocation]


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
    target_pointer = struct.unpack_from(">I", image, TARGET_POINTER_OFFSET)[0]
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
    expected_changed = [POINTER_OFFSET + 2, POINTER_OFFSET + 3]
    if changed != expected_changed:
        raise AssertionError(f"unexpected changed offsets: {changed}")

    patched_sector = bytes(patched[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(patched_sector) != PATCHED_SECTOR_CRC32B:
        raise AssertionError("patched sector CRC no longer matches the fixed helpers")

    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-valid-cross-bank-pointer-redirection",
        "source": {"size_bytes": len(image), "sha256": digest},
        "target": {
            "source_bank": "English table carrying installed Swedish payloads",
            "target_bank": "Français",
            "entry_index": ENTRY_INDEX,
            "pointer_offset": f"0x{POINTER_OFFSET:06x}",
            "pointer_before": f"0x{SOURCE_RELATIVE:08x}",
            "pointer_after": f"0x{TARGET_RELATIVE:08x}",
            "source_record": f"0x{SOURCE_RECORD:06x}",
            "target_record": f"0x{TARGET_RECORD:06x}",
            "source_allocation": source_allocation,
            "target_allocation": target_allocation,
            "source_text": "Huvudmeny",
            "target_text": "Menu principal",
            "changed_offsets": [f"0x{offset:06x}" for offset in expected_changed],
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
            "only_two_pointer_bytes_differ": True,
            "string_payload_bytes_modified": False,
            "length_prefixes_modified": False,
            "target_is_existing_valid_record": True,
            "target_is_outside_source_bank": True,
        },
        "expected_observation": {
            "main_menu_title": "Menu principal",
            "if_observed": "The relative pointer is not constrained to the source bank.",
        },
        "safety": {
            "source_image_modified": False,
            "write_not_authorized_by_manifest": True,
            "required_before_write": [
                "normal charger cold start",
                "live sector CRC equals f5c23372",
                "JEDEC ID equals 1c3016",
                "cross-bank SRAM payload CRC equals b29ee7d1",
                "cross-bank-specific restoration helper passes a physical no-op gate",
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
        "patched_sector": args.output_dir / "crossbank-sector-003000.bin",
        "patch_chunk_0": args.output_dir / "crossbank-sector-003000-chunk0.bin",
        "patch_chunk_1": args.output_dir / "crossbank-sector-003000-chunk1.bin",
        "patch_chunk_2": args.output_dir / "crossbank-sector-003000-chunk2.bin",
        "patch_chunk_3": args.output_dir / "crossbank-sector-003000-chunk3.bin",
        "restore_sector": args.output_dir / "restore-sector-003000.bin",
        "restore_chunk_0": args.output_dir / "restore-sector-003000-chunk0.bin",
        "restore_chunk_1": args.output_dir / "restore-sector-003000-chunk1.bin",
        "restore_chunk_2": args.output_dir / "restore-sector-003000-chunk2.bin",
        "restore_chunk_3": args.output_dir / "restore-sector-003000-chunk3.bin",
        "patched_image": args.output_dir / "crossbank-probe-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patched_sector"].write_bytes(patched_sector)
    outputs["restore_sector"].write_bytes(original_sector)
    for index in range(4):
        outputs[f"patch_chunk_{index}"].write_bytes(
            patched_sector[index * 0x400 : (index + 1) * 0x400]
        )
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
