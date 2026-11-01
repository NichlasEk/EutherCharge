#!/usr/bin/env python3
"""Prepare a bounded shortening of the KW520 main-title allocation field."""

from __future__ import annotations

import argparse
import hashlib
import json
import zlib
from pathlib import Path


IMAGE_SIZE = 4 * 1024 * 1024
INSTALLED_SHA256 = "4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329"
SECTOR_BASE = 0x003000
SECTOR_SIZE = 0x1000
LENGTH_OFFSET = 0x003892
PAYLOAD_OFFSET = 0x003894
BEFORE = bytes.fromhex("000a")
AFTER = bytes.fromhex("0008")
PAYLOAD = b"Huvudmeny\0"
ORIGINAL_SECTOR_CRC32B = 0xF5C23372
PATCHED_SECTOR_CRC32B = 0x5E1E3B15


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def prepare(image: bytes) -> tuple[bytes, bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"image is {len(image)} bytes, expected {IMAGE_SIZE}")
    digest = sha256(image)
    if digest != INSTALLED_SHA256:
        raise ValueError(
            "refusing an unknown base image: "
            f"SHA-256 {digest}, expected installed image {INSTALLED_SHA256}"
        )
    if image[LENGTH_OFFSET : LENGTH_OFFSET + 2] != BEFORE:
        raise ValueError("main-title length precondition failed")
    if image[PAYLOAD_OFFSET : PAYLOAD_OFFSET + len(PAYLOAD)] != PAYLOAD:
        raise ValueError("main-title payload precondition failed")
    if any((old & new) != new for old, new in zip(BEFORE, AFTER, strict=True)):
        raise AssertionError("length probe contains a forbidden 0-to-1 transition")

    original_sector = image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE]
    if crc32b(original_sector) != ORIGINAL_SECTOR_CRC32B:
        raise ValueError("original sector CRC precondition failed")
    patched = bytearray(image)
    patched[LENGTH_OFFSET : LENGTH_OFFSET + 2] = AFTER
    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    if changed != [LENGTH_OFFSET + 1]:
        raise AssertionError(f"unexpected changed offsets: {changed}")
    patched_sector = bytes(patched[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    if crc32b(patched_sector) != PATCHED_SECTOR_CRC32B:
        raise AssertionError("patched sector CRC no longer matches fixed helpers")

    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-main-title-declared-length-shortening",
        "source": {"size_bytes": len(image), "sha256": digest},
        "target": {
            "record_offset": f"0x{LENGTH_OFFSET:06x}",
            "payload_offset": f"0x{PAYLOAD_OFFSET:06x}",
            "length_before": 10,
            "length_after": 8,
            "changed_offset": f"0x{LENGTH_OFFSET + 1:06x}",
            "changed_byte_before": "0x0a",
            "changed_byte_after": "0x08",
            "bit_transitions": "1-to-0-only",
            "payload_hex": PAYLOAD.hex(),
            "payload_modified": False,
            "sector_erase_required_for_probe": False,
        },
        "hashes": {
            "original_sector_sha256": sha256(original_sector),
            "original_sector_crc32b": f"{crc32b(original_sector):08x}",
            "patched_sector_sha256": sha256(patched_sector),
            "patched_sector_crc32b": f"{crc32b(patched_sector):08x}",
            "patched_full_image_sha256": sha256(bytes(patched)),
        },
        "expected_observation": {
            "nul_only_reader": "Huvudmeny",
            "eight_byte_copy_without_added_nul": "Huvudmen",
            "length_minus_nul_copy": "Huvudme",
            "note": "Other bounded display output is recorded without inferring a vulnerability.",
        },
        "safety": {
            "source_image_modified": False,
            "copy_length_only_decreases": True,
            "page_program_bytes": 2,
            "restore_requires_sector_erase": True,
            "write_not_authorized_by_manifest": True,
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
        "patched_sector": args.output_dir / "length-sector-003000.bin",
        "restore_sector": args.output_dir / "restore-sector-003000.bin",
        "restore_chunk_0": args.output_dir / "restore-sector-003000-chunk0.bin",
        "restore_chunk_1": args.output_dir / "restore-sector-003000-chunk1.bin",
        "restore_chunk_2": args.output_dir / "restore-sector-003000-chunk2.bin",
        "restore_chunk_3": args.output_dir / "restore-sector-003000-chunk3.bin",
        "patched_image": args.output_dir / "length-probe-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patched_sector"].write_bytes(patched_sector)
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
