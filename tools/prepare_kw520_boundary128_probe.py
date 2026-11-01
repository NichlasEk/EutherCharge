#!/usr/bin/env python3
"""Prepare a two-sector allocation-128 KW520 string-boundary probe."""

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
POINTER_BEFORE = 0x00000692
TEST_RECORD = 0x00C000
POINTER_AFTER = TEST_RECORD - POINTER_BASE
POINTER_SECTOR = 0x003000
DATA_SECTOR = 0x00C000
SECTOR_SIZE = 0x1000
VISIBLE = (b"E128-" + (b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5))[:126] + b"Z"
PAYLOAD = VISIBLE + b"\0"
RECORD = struct.pack(">H", len(PAYLOAD)) + PAYLOAD
POINTER_ORIGINAL_CRC32B = 0xF5C23372
POINTER_TEST_CRC32B = 0x6F68933F
DATA_ORIGINAL_CRC32B = 0xF154670A
DATA_TEST_CRC32B = 0x1F18AA83

assert len(VISIBLE) == 127
assert len(PAYLOAD) == 128
assert POINTER_AFTER == 0x00008E00


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
    pointer = struct.unpack_from(">I", image, POINTER_OFFSET)[0]
    if pointer != POINTER_BEFORE:
        raise ValueError(f"title pointer is 0x{pointer:08x}, expected 0x{POINTER_BEFORE:08x}")

    pointer_original = image[POINTER_SECTOR : POINTER_SECTOR + SECTOR_SIZE]
    data_original = image[DATA_SECTOR : DATA_SECTOR + SECTOR_SIZE]
    if crc32b(pointer_original) != POINTER_ORIGINAL_CRC32B:
        raise ValueError("pointer-sector CRC precondition failed")
    if data_original != b"\xff" * SECTOR_SIZE or crc32b(data_original) != DATA_ORIGINAL_CRC32B:
        raise ValueError("data-sector all-FF precondition failed")

    pointer_test = bytearray(pointer_original)
    struct.pack_into(">I", pointer_test, POINTER_OFFSET - POINTER_SECTOR, POINTER_AFTER)
    data_test = bytearray(data_original)
    data_test[: len(RECORD)] = RECORD
    if crc32b(pointer_test) != POINTER_TEST_CRC32B:
        raise AssertionError("pointer-test CRC no longer matches fixed helper")
    if crc32b(data_test) != DATA_TEST_CRC32B:
        raise AssertionError("data-test CRC no longer matches fixed helper")

    patched = bytearray(image)
    patched[POINTER_SECTOR : POINTER_SECTOR + SECTOR_SIZE] = pointer_test
    patched[DATA_SECTOR : DATA_SECTOR + SECTOR_SIZE] = data_test
    changes = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    pointer_changes = [POINTER_OFFSET + 2, POINTER_OFFSET + 3]
    expected_changes = pointer_changes + list(range(DATA_SECTOR, DATA_SECTOR + len(RECORD)))
    if changes != expected_changes:
        raise AssertionError("unexpected image changes")

    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-allocation-128-two-sector-string-boundary-probe",
        "source": {"size_bytes": len(image), "sha256": digest},
        "record": {
            "offset": f"0x{TEST_RECORD:06x}",
            "relative_pointer": f"0x{POINTER_AFTER:08x}",
            "allocation": len(PAYLOAD),
            "visible_payload_bytes": len(VISIBLE),
            "visible_ascii": VISIBLE.decode("ascii"),
            "payload_sha256": sha256(PAYLOAD),
            "record_sha256": sha256(RECORD),
            "terminator_inside_allocation": True,
            "known_physically_accepted_allocation": 114,
            "bytes_above_known_accepted_allocation": 14,
        },
        "pointer": {
            "offset": f"0x{POINTER_OFFSET:06x}",
            "before": f"0x{POINTER_BEFORE:08x}",
            "after": f"0x{POINTER_AFTER:08x}",
            "changed_offsets": [f"0x{value:06x}" for value in pointer_changes],
            "identical_to_allocation_114_probe": True,
        },
        "hashes": {
            "pointer_original_crc32b": f"{crc32b(pointer_original):08x}",
            "pointer_original_sha256": sha256(pointer_original),
            "pointer_test_crc32b": f"{crc32b(pointer_test):08x}",
            "pointer_test_sha256": sha256(pointer_test),
            "data_original_crc32b": f"{crc32b(data_original):08x}",
            "data_original_sha256": sha256(data_original),
            "data_test_crc32b": f"{crc32b(data_test):08x}",
            "data_test_sha256": sha256(data_test),
            "patched_full_image_sha256": sha256(bytes(patched)),
        },
        "invariants": {
            "data_sector_was_all_ff": True,
            "data_sector_is_outside_all_active_resource_banks": True,
            "pointer_sector_only_two_bytes_differ": True,
            "active_neighbor_record_modified": False,
            "power_or_calibration_data_modified": False,
            "source_image_modified": False,
        },
        "recovery_order": [
            "restore pointer sector 0x003000 first",
            "cold-start and confirm normal Huvudmeny",
            "restore data sector 0x00c000 to exact all-FF",
        ],
        "safety": {
            "write_not_authorized_by_manifest": True,
            "each_data_state_requires_distinct_address-and-CRC-locked-helper": True,
            "pointer_helpers_are_byte-identical_to_physically_qualified_allocation_114_helpers": True,
            "raw_runtime_sram_must_remain_ignored": True,
        },
    }
    return bytes(patched), pointer_original, bytes(pointer_test), data_original, bytes(data_test), manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    patched, pointer_original, pointer_test, data_original, data_test, manifest = prepare(args.image.read_bytes())
    sectors = {
        "pointer-original": ("003000", pointer_original),
        "pointer-test": ("003000", pointer_test),
        "data-original": ("00c000", data_original),
        "data-test": ("00c000", data_test),
    }
    outputs: dict[str, Path] = {
        "patched_image": args.output_dir / "boundary128-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    for prefix, (address, _sector) in sectors.items():
        outputs[prefix] = args.output_dir / f"{prefix}-sector-{address}.bin"
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"] = args.output_dir / f"{prefix}-sector-{address}-chunk{index}.bin"
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patched_image"].write_bytes(patched)
    for prefix, (_address, sector) in sectors.items():
        outputs[prefix].write_bytes(sector)
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"].write_bytes(sector[index * 0x400 : (index + 1) * 0x400])
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
