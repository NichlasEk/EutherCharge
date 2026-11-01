#!/usr/bin/env python3
"""Prepare the exact reversible 8-to-9 KW520 language-directory probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


IMAGE_SIZE = 4 * 1024 * 1024
SECTOR_START = 0x3000
SECTOR_SIZE = 0x1000
DIRECTORY_START = 0x3200
SLOT_START = 0x3201
SLOT_SIZE = 19
SOURCE_SLOT = 8
TEST_SLOT = 9
EXPECTED_IMAGE_SHA256 = "4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329"
EXPECTED_SECTOR_CRC32 = 0xF5C23372
EXPECTED_PROBE_CRC32 = 0xFA2D76BB
EXPECTED_ACTIVE_IDS = (3, 4, 5, 6, 7, 8, 10, 14)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def slot_offset(slot: int) -> int:
    return SLOT_START + slot * SLOT_SIZE


def decode_slot(raw: bytes) -> dict[str, int]:
    language_id, ordinary_table, ordinary_count, dtc_table, dtc_count, third_table, third_count = struct.unpack(
        ">BIHIHIH", raw
    )
    return {
        "language_id": language_id,
        "ordinary_table_relative": ordinary_table,
        "ordinary_count": ordinary_count,
        "dtc_table_relative": dtc_table,
        "dtc_count": dtc_count,
        "third_table_relative": third_table,
        "third_count": third_count,
    }


def validate_pointer_targets(image: bytes, entry: dict[str, int]) -> None:
    ordinary = DIRECTORY_START + entry["ordinary_table_relative"]
    assert entry["ordinary_count"] == 162
    assert 0 <= ordinary <= len(image) - entry["ordinary_count"] * 4
    for index in range(entry["ordinary_count"]):
        relative = struct.unpack_from(">I", image, ordinary + index * 4)[0]
        record = DIRECTORY_START + relative
        assert 0 <= record <= len(image) - 2
        allocation = struct.unpack_from(">H", image, record)[0]
        payload = image[record + 2:record + 2 + allocation]
        assert len(payload) == allocation and payload[-1:] == b"\0"

    dtc = DIRECTORY_START + entry["dtc_table_relative"]
    assert entry["dtc_count"] == 1
    assert 0 <= dtc <= len(image) - 7
    relative = struct.unpack_from(">I", image, dtc + 3)[0]
    record = DIRECTORY_START + relative
    allocation = struct.unpack_from(">H", image, record)[0]
    payload = image[record + 2:record + 2 + allocation]
    assert len(payload) == allocation and payload[-1:] == b"\0"
    assert entry["third_count"] == 0


def prepare(image: bytes) -> tuple[bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"expected {IMAGE_SIZE} bytes, got {len(image)}")
    digest = sha256(image)
    if digest != EXPECTED_IMAGE_SHA256:
        raise ValueError(f"refusing unqualified image SHA-256 {digest}")

    original = image[SECTOR_START:SECTOR_START + SECTOR_SIZE]
    if crc32(original) != EXPECTED_SECTOR_CRC32:
        raise ValueError("refusing unexpected source sector CRC32")
    if image[DIRECTORY_START] != len(EXPECTED_ACTIVE_IDS):
        raise ValueError("refusing unexpected declared language count")

    active: list[int] = []
    entries: dict[int, dict[str, int]] = {}
    for slot in range(15):
        start = slot_offset(slot)
        raw = image[start:start + SLOT_SIZE]
        if raw == b"\xff" * SLOT_SIZE:
            continue
        entry = decode_slot(raw)
        if entry["language_id"] != slot:
            raise ValueError(f"slot {slot} language ID mismatch")
        validate_pointer_targets(image, entry)
        active.append(slot)
        entries[slot] = entry
    if tuple(active) != EXPECTED_ACTIVE_IDS:
        raise ValueError(f"refusing active language IDs {active}")

    test_start = slot_offset(TEST_SLOT)
    if image[test_start:test_start + SLOT_SIZE] != b"\xff" * SLOT_SIZE:
        raise ValueError("refusing non-erased test slot 9")
    source_start = slot_offset(SOURCE_SLOT)
    source_raw = image[source_start:source_start + SLOT_SIZE]

    probe = bytearray(original)
    probe[DIRECTORY_START - SECTOR_START] = 9
    relative_test = test_start - SECTOR_START
    probe[relative_test:relative_test + SLOT_SIZE] = bytes([TEST_SLOT]) + source_raw[1:]
    probe = bytes(probe)
    if crc32(probe) != EXPECTED_PROBE_CRC32:
        raise AssertionError("derived probe CRC32 changed")

    changed = [
        {"absolute_offset": f"0x{SECTOR_START + index:06x}", "before": before, "after": after}
        for index, (before, after) in enumerate(zip(original, probe))
        if before != after
    ]
    duplicate = decode_slot(probe[relative_test:relative_test + SLOT_SIZE])
    if duplicate["language_id"] != TEST_SLOT or duplicate | {"language_id": SOURCE_SLOT} != entries[SOURCE_SLOT]:
        raise AssertionError("slot 9 is not an exact slot-8 resource duplicate")
    validate_pointer_targets(image, duplicate)

    manifest: dict[str, object] = {
        "purpose": "reversible language-directory 8-to-9 parser gate",
        "source_image": {"sha256": digest, "size": len(image)},
        "sector": {
            "address": f"0x{SECTOR_START:06x}",
            "size": SECTOR_SIZE,
            "original_crc32": f"{crc32(original):08x}",
            "probe_crc32": f"{crc32(probe):08x}",
            "original_sha256": sha256(original),
            "probe_sha256": sha256(probe),
        },
        "directory": {
            "count_offset": f"0x{DIRECTORY_START:06x}",
            "count_before": 8,
            "count_after": 9,
            "active_ids_before": list(EXPECTED_ACTIVE_IDS),
            "active_ids_after": [3, 4, 5, 6, 7, 8, 9, 10, 14],
            "source_slot": SOURCE_SLOT,
            "test_slot": TEST_SLOT,
            "test_slot_offset": f"0x{test_start:06x}",
            "test_entry": duplicate,
            "all_targets_validated": True,
        },
        "changed_bytes": changed,
        "write_order": [
            "install exact CRC-gated sector 0x003000",
            "cold-start and inspect language menu",
            "restore exact original sector 0x003000",
            "cold-start and verify Huvudmeny plus buttons",
        ],
    }
    return original, probe, manifest


def write_chunks(output: Path, stem: str, sector: bytes) -> None:
    for index in range(4):
        chunk = sector[index * 0x400:(index + 1) * 0x400]
        (output / f"{stem}-chunk{index}.bin").write_bytes(chunk)


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
    (args.output / "language9-test-sector-003000.bin").write_bytes(probe)
    write_chunks(args.output, "original-sector-003000", original)
    write_chunks(args.output, "language9-test-sector-003000", probe)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
