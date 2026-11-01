#!/usr/bin/env python3
"""Prepare fixed direct transitions between qualified KW520 boundary records."""

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
POINTER_ORIGINAL_CRC32B = 0xF5C23372
POINTER_TEST_CRC32B = 0x6F68933F

# Each allowed edge is explicit; this is not a general arbitrary writer.
ALLOWED_TRANSITIONS = {(160, 192), (192, 224), (224, 240)}
FIXED = {
    160: {
        "crc32b": 0x0C91E3D5,
        "payload_sha256": "cc07b25c0b24fece5cc78767e659bca8209d6f6ecf0b92dcc6836b5ce5a420c5",
        "record_sha256": "67d1e8ea0a507630bb0a0ffc9343883eb195d0eefcfd95d2ddd5d08971f7549c",
        "sector_sha256": "4b8c14f8008e650fdfd8cdb679451d4bab2d69898eb43d55ea40c068c28fdfe7",
    },
    192: {
        "crc32b": 0x80FFF2A8,
        "payload_sha256": "0643c6a027583c09e678f6db6c5ac74ff3b66ebd34c126b3215703219e4d0d52",
        "record_sha256": "f841271a5c56d2b4a9e6117ed7946f67f7c8f5283f953df47a1f82db5ad994dc",
        "sector_sha256": "6190f192cf0346aff5f7dc2ce0de5c7819e8d9ecaf496830a301ef4ad86226cd",
    },
    224: {
        "crc32b": 0xFF988D5C,
        "payload_sha256": "00fb47e3c27626ba7d9a6f1aa3b07443c4d98b2de561c0d34b62724b881a9998",
        "record_sha256": "dba3f724996b6e1dace9193cd31bbee470ce98db54d6dd34d648dfbaef29d92c",
        "sector_sha256": "6df7f0b56e7941a05b16b8be6e4297ed86eb17f09e4b6acb95a10128510d849b",
    },
    240: {
        "crc32b": 0xABA2265E,
        "payload_sha256": "447817ede04a64f5fb0190b27f0f3a5523321913dca4c7a2b7d27ecb81329ed5",
        "record_sha256": "6e9da64ad49bf0110800b4c0a1649ddf645daccd031b48d7684ccfcf264b07b2",
        "sector_sha256": "dda9adf54f387a17957b0a0337fd671e2cd48853fe3a6fcb107701a1d4b41b45",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def record_for(allocation: int) -> tuple[bytes, bytes, bytes]:
    visible = (f"E{allocation}-".encode("ascii") + b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 8)[: allocation - 2] + b"Z"
    payload = visible + b"\0"
    record = struct.pack(">H", allocation) + payload
    sector = record + b"\xff" * (SECTOR_SIZE - len(record))
    expected = FIXED[allocation]
    if len(payload) != allocation or crc32b(sector) != expected["crc32b"]:
        raise AssertionError(f"fixed allocation-{allocation} construction changed")
    if sha256(payload) != expected["payload_sha256"] or sha256(record) != expected["record_sha256"] or sha256(sector) != expected["sector_sha256"]:
        raise AssertionError(f"fixed allocation-{allocation} hashes changed")
    return visible, payload, sector


def prepare(image: bytes, source_allocation: int, target_allocation: int) -> tuple[dict[str, bytes], dict[str, object]]:
    if (source_allocation, target_allocation) not in ALLOWED_TRANSITIONS:
        raise ValueError("refusing transition outside fixed adjacent boundary profiles")
    if len(image) != IMAGE_SIZE or sha256(image) != INSTALLED_SHA256:
        raise ValueError("refusing unknown base image")
    if struct.unpack_from(">I", image, POINTER_OFFSET)[0] != POINTER_BEFORE:
        raise ValueError("base-image title pointer precondition failed")
    pointer_original = image[POINTER_SECTOR : POINTER_SECTOR + SECTOR_SIZE]
    if crc32b(pointer_original) != POINTER_ORIGINAL_CRC32B:
        raise ValueError("pointer-sector CRC precondition failed")
    if image[DATA_SECTOR : DATA_SECTOR + SECTOR_SIZE] != b"\xff" * SECTOR_SIZE:
        raise ValueError("base-image data-sector all-FF precondition failed")

    pointer_test = bytearray(pointer_original)
    struct.pack_into(">I", pointer_test, POINTER_OFFSET - POINTER_SECTOR, POINTER_AFTER)
    if crc32b(pointer_test) != POINTER_TEST_CRC32B:
        raise AssertionError("pointer-test CRC changed")
    _source_visible, _source_payload, source_sector = record_for(source_allocation)
    visible, payload, target_sector = record_for(target_allocation)
    patched = bytearray(image)
    patched[POINTER_SECTOR : POINTER_SECTOR + SECTOR_SIZE] = pointer_test
    patched[DATA_SECTOR : DATA_SECTOR + SECTOR_SIZE] = target_sector
    sectors = {
        "pointer-original": pointer_original,
        "pointer-test": bytes(pointer_test),
        "data-original": b"\xff" * SECTOR_SIZE,
        "data-previous": source_sector,
        "data-test": target_sector,
    }
    manifest: dict[str, object] = {
        "format": 1,
        "operation": f"kw520-direct-allocation-{source_allocation}-to-{target_allocation}-boundary-probe",
        "source": {"size_bytes": len(image), "sha256": sha256(image)},
        "record": {
            "offset": f"0x{TEST_RECORD:06x}",
            "relative_pointer": f"0x{POINTER_AFTER:08x}",
            "allocation": target_allocation,
            "visible_payload_bytes": len(visible),
            "visible_ascii": visible.decode("ascii"),
            "payload_sha256": sha256(payload),
            "terminator_inside_allocation": True,
        },
        "transition": {
            "from_allocation": source_allocation,
            "from_crc32b": f"{crc32b(source_sector):08x}",
            "to_allocation": target_allocation,
            "to_crc32b": f"{crc32b(target_sector):08x}",
            "all_ff_intermediate_required": False,
            "pointer_must_be_original_before_transition": True,
        },
        "hashes": {name.replace("-", "_") + "_sha256": sha256(data) for name, data in sectors.items()},
        "recovery_order": [
            "restore pointer sector 0x003000 first",
            "cold-start and confirm normal Huvudmeny",
            "restore data sector 0x00c000 only at final cleanup",
        ],
        "safety": {
            "write_not_authorized_by_manifest": True,
            "only_fixed_adjacent_transition_is_generated": True,
            "status_clear_attempts_are_bounded_to_two_in_writer": True,
            "raw_runtime_sram_must_remain_ignored": True,
        },
        "patched_full_image_sha256": sha256(bytes(patched)),
    }
    return sectors, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--from-allocation", type=int, required=True)
    parser.add_argument("--to-allocation", type=int, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    sectors, manifest = prepare(args.image.read_bytes(), args.from_allocation, args.to_allocation)
    outputs: dict[str, Path] = {"manifest": args.output_dir / "manifest.json"}
    for prefix in sectors:
        address = "003000" if prefix.startswith("pointer") else "00c000"
        outputs[prefix] = args.output_dir / f"{prefix}-sector-{address}.bin"
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"] = args.output_dir / f"{prefix}-sector-{address}-chunk{index}.bin"
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for prefix, sector in sectors.items():
        outputs[prefix].write_bytes(sector)
        for index in range(4):
            outputs[f"{prefix}_chunk_{index}"].write_bytes(sector[index * 0x400 : (index + 1) * 0x400])
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
