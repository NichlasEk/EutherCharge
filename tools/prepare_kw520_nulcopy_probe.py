#!/usr/bin/env python3
"""Prepare the fixed embedded-NUL KW520 copy-semantics diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


IMAGE_SIZE = 4 * 1024 * 1024
INSTALLED_SHA256 = "4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329"
POINTER_BASE = 0x3200
POINTER_OFFSET = 0x3604
POINTER_BEFORE = 0x00000692
POINTER_AFTER = 0x00C000 - POINTER_BASE
POINTER_SECTOR = 0x3000
DATA_SECTOR = 0xC000
SECTOR_SIZE = 0x1000
ALLOCATION = 320
EMBEDDED_NUL = 100
RETURN_OFFSET = 252
RETURN_WORD = 0x080093F3
COPY_LIMIT = 256
BUFFER_ADDRESS = 0x20003978


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def repeated(token: bytes, length: int) -> bytes:
    return (token * ((length + len(token) - 1) // len(token)))[:length]


def build_payload() -> bytes:
    payload = bytearray(repeated(b"NUL-COPY-GATE-", ALLOCATION))
    payload[EMBEDDED_NUL] = 0
    payload[EMBEDDED_NUL + 1:RETURN_OFFSET] = repeated(
        b"AFTER-NUL-MARKER-", RETURN_OFFSET - EMBEDDED_NUL - 1
    )
    struct.pack_into("<I", payload, RETURN_OFFSET, RETURN_WORD)
    payload[COPY_LIMIT:ALLOCATION - 1] = repeated(b"TAIL-UNREAD-", ALLOCATION - 1 - COPY_LIMIT)
    payload[-1] = 0
    return bytes(payload)


def prepare(image: bytes) -> tuple[dict[str, bytes], dict[str, object]]:
    if len(image) != IMAGE_SIZE or sha256(image) != INSTALLED_SHA256:
        raise ValueError("refusing unknown base image")
    if struct.unpack_from(">I", image, POINTER_OFFSET)[0] != POINTER_BEFORE:
        raise ValueError("base-image title pointer precondition failed")
    pointer_original = image[POINTER_SECTOR:POINTER_SECTOR + SECTOR_SIZE]
    if crc32(pointer_original) != 0xF5C23372:
        raise ValueError("pointer-sector CRC precondition failed")
    data_original = image[DATA_SECTOR:DATA_SECTOR + SECTOR_SIZE]
    if data_original != b"\xff" * SECTOR_SIZE:
        raise ValueError("data-sector all-FF precondition failed")

    pointer_probe = bytearray(pointer_original)
    struct.pack_into(">I", pointer_probe, POINTER_OFFSET - POINTER_SECTOR, POINTER_AFTER)
    if crc32(pointer_probe) != 0x6F68933F:
        raise AssertionError("pointer-probe CRC changed")

    payload = build_payload()
    if len(payload) != ALLOCATION or payload[EMBEDDED_NUL] != 0 or payload[-1] != 0:
        raise AssertionError("payload boundary changed")
    if struct.unpack_from("<I", payload, RETURN_OFFSET)[0] != RETURN_WORD:
        raise AssertionError("preserved return word changed")
    record = struct.pack(">H", ALLOCATION) + payload
    data_probe = record + b"\xff" * (SECTOR_SIZE - len(record))
    sectors = {
        "pointer-original-sector-003000": pointer_original,
        "pointer-test-sector-003000": bytes(pointer_probe),
        "data-original-sector-00c000": data_original,
        "nulcopy-data-test-sector-00c000": data_probe,
    }
    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-embedded-nul-copy-semantics",
        "source": {"size": len(image), "sha256": sha256(image)},
        "record": {
            "address": "0x00c000",
            "allocation": ALLOCATION,
            "buffer_address": f"0x{BUFFER_ADDRESS:08x}",
            "embedded_nul_offset": EMBEDDED_NUL,
            "marker_after_nul_offset": EMBEDDED_NUL + 1,
            "copy_limit": COPY_LIMIT,
            "return_word_offset": RETURN_OFFSET,
            "return_word_address": f"0x{BUFFER_ADDRESS + RETURN_OFFSET:08x}",
            "return_word_little_endian": payload[RETURN_OFFSET:RETURN_OFFSET + 4].hex(),
            "return_word": f"0x{RETURN_WORD:08x}",
            "final_nul_offset": ALLOCATION - 1,
        },
        "sector": {
            "original_crc32": f"{crc32(data_original):08x}",
            "probe_crc32": f"{crc32(data_probe):08x}",
            "original_sha256": sha256(data_original),
            "probe_sha256": sha256(data_probe),
        },
        "expected_sram_discriminator": {
            "fixed_size_copy": "AFTER-NUL-MARKER bytes survive after payload offset 100",
            "stop_at_nul": "bytes after offset 100 retain pre-copy SRAM contents",
            "zero_padding": "bytes after offset 100 are zero through the fixed copy width",
        },
        "safety": {
            "no_chosen_control_target": True,
            "recurrent_return_word_preserved_exactly": True,
            "return_word_observed_in_comparable_captures": 9,
            "pointer_must_be_restored_before_data_sector": True,
        },
    }
    return sectors, manifest


def write_chunks(output: Path, name: str, sector: bytes) -> None:
    (output / f"{name}.bin").write_bytes(sector)
    for index in range(4):
        (output / f"{name}-chunk{index}.bin").write_bytes(sector[index * 0x400:(index + 1) * 0x400])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    args.output.mkdir(parents=True, exist_ok=True)
    sectors, manifest = prepare(args.image.read_bytes())
    for name, sector in sectors.items():
        write_chunks(args.output, name, sector)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
