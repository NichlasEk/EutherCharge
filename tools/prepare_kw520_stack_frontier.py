#!/usr/bin/env python3
"""Prepare only the fixed KW520 cyclic stack-frontier profiles."""

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
ALLOCATIONS = (256, 320, 384, 448, 480, 512)
FIXED = {
    256: (0x28017863, "20f9601c5cad1ae5068e1fefb246fd7945766ccd9e6db1405d8679f2675d8696", "87cb84e384367db72bb47e72b66a5645df1a305917bf0e8a1ff77d94e52be0a4", "9ceaa4a5a35c555005051a7686af9b32ca9188227f12d84e62afda8d84706ebe", "8e24beb9d748611fea4c191ac5de47d21ce874de14ec0d20c282d40602d0e7b8"),
    320: (0x41B76A28, "9168157387d99a0f00f2cb7d59edddd6446239b60fa45cf6b38921465d944cae", "27753b6c08b9a31cffa9e5bc23a4e2c4dab2c5df4485bbd0c4ea5ad4ec3aee64", "78a2d9c9575c900b17ab77d23d363564d70cf39266d8affaab518c0ced63ba06", "0f04c18e02b90755014db47fd0a7dfd9f6fdee599b0ebd0c6d673af6e51a852a"),
    384: (0x52FDFC69, "b999a74f85a19c513d0b072bf0cf9be17828a2b8b9e4a800793f15d5c6d415f0", "4e872614fd43244674421d945a559009253b06756cfd7ba8c7bc50c6dc34392d", "bd42e78db14fbec69212f8783da7a7bd616dd066c94954cc1cb4047f747e7ac0", "41d3bdb3cc6e6ce5cad9d9b04ac371dfca53380a3701d2d69a645cf05decbb62"),
    448: (0x7CFE1846, "a4d096a862f8dac4f180f21e2568501ef52713aee8b606e9713d0f4e1e9aee8a", "33b82b4780ad61b905875ada09cb00c36dcdad46b0aaa3472d01db0aa51957fa", "97b99c805fcb52a08c83905e4cac3e3c7e3ebe93b0b525cc39a4305f2587ead1", "e332c967d0097bacfa4cbd62e726b96772b3ee0e4b19972f5699dffc947f9f82"),
    480: (0xEBDAF776, "5dc8711f2137728d33448206602a092db283851be53b40ad28fdf81206917df2", "e7bba2121ae2f6c1246ea20f0a5eea9f31818052c0fa58a78691c34253506d84", "61675b6a7f150919d93cbf19d54ccc1ce5ca8dbf45f7b7c6a23aa8262613c73d", "ed7e236286070c3e3addf21b2fc156de21337c375e9b449d712f823d5a3cbe2c"),
    512: (0x72628A3A, "ffd86f4bcb87bf291f82c83e10b9b4fd4a5241d32d3d0adfcc7fe9e1916124f8", "8fc6ee07f2c42768155385d3204b093c061b39c1bd078990ad60d0e7eca57379", "6eb076164bb664b0ae5d591a1842745aaa7753e44ae4939d06e38645894b5960", "505883a649f7d8bbb679c18a0bd315b47f4c273f431e9800ec1368804747b8e8"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def cyclic(length: int) -> bytes:
    alphabet = b"abcdefghijklmnopqrstuvwxyz0123456789"
    order = 4
    work = [0] * (len(alphabet) * order)
    output: list[int] = []

    def build(position: int, period: int) -> None:
        if position > order:
            if order % period == 0:
                output.extend(work[1 : period + 1])
            return
        work[position] = work[position - period]
        build(position + 1, period)
        for symbol in range(work[position - period] + 1, len(alphabet)):
            work[position] = symbol
            build(position + 1, position)

    build(1, 1)
    if length > len(output):
        raise ValueError("requested cyclic pattern exceeds fixed alphabet")
    return bytes(alphabet[index] for index in output[:length])


def record_for(allocation: int) -> tuple[bytes, bytes, bytes, bytes]:
    if allocation not in ALLOCATIONS:
        raise ValueError("refusing allocation outside fixed stack-frontier profiles")
    visible = cyclic(allocation - 1)
    payload = visible + b"\0"
    record = struct.pack(">H", allocation) + payload
    sector = record + b"\xff" * (SECTOR_SIZE - len(record))
    expected = FIXED[allocation]
    actual = (crc32b(sector), sha256(visible), sha256(payload), sha256(record), sha256(sector))
    if actual != expected:
        raise AssertionError(f"fixed allocation-{allocation} construction changed")
    return visible, payload, record, sector


def prepare(image: bytes) -> tuple[dict[str, bytes], dict[int, dict[str, object]]]:
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

    sectors = {
        "pointer-original-sector-003000": pointer_original,
        "pointer-test-sector-003000": bytes(pointer_test),
        "data-original-sector-00c000": b"\xff" * SECTOR_SIZE,
    }
    manifests: dict[int, dict[str, object]] = {}
    for allocation in ALLOCATIONS:
        visible, payload, record, sector = record_for(allocation)
        name = f"alloc-{allocation}-data-test-sector-00c000"
        sectors[name] = sector
        manifests[allocation] = {
            "format": 1,
            "operation": "kw520-cyclic-stack-frontier",
            "source": {"size_bytes": len(image), "sha256": sha256(image)},
            "record": {
                "offset": f"0x{TEST_RECORD:06x}",
                "relative_pointer": f"0x{POINTER_AFTER:08x}",
                "allocation": allocation,
                "visible_payload_bytes": len(visible),
                "buffer_start": "0x20003978",
                "expected_end_exclusive": f"0x{0x20003978 + allocation:08x}",
                "visible_sha256": sha256(visible),
                "payload_sha256": sha256(payload),
                "record_sha256": sha256(record),
                "sector_sha256": sha256(sector),
                "sector_crc32b": f"{crc32b(sector):08x}",
                "terminator_inside_allocation": True,
                "payload_is_ascii_cyclic_only": True,
            },
            "hashes": {
                "pointer_original_sha256": sha256(pointer_original),
                "pointer_test_sha256": sha256(bytes(pointer_test)),
                "data_original_sha256": sha256(sectors["data-original-sector-00c000"]),
                "data_test_sha256": sha256(sector),
            },
            "recovery_order": [
                "capture SRAM/register/fault evidence without target SRAM writes",
                "restore pointer sector 0x003000 through fixed bitbang recovery",
                "cold-start and confirm normal Huvudmeny",
                "restore data sector 0x00c000 to exact all-FF",
                "cold-start and confirm normal Huvudmeny again",
            ],
            "safety": {
                "write_not_authorized_by_manifest": True,
                "only_fixed_allocation_is_generated": True,
                "no_percent_or_nul_inside_visible_payload": b"%" not in visible and b"\0" not in visible,
                "cyclic_words_do_not_encode_sram_flash_or_peripheral_addresses": True,
                "raw_runtime_sram_must_remain_ignored": True,
            },
        }
    return sectors, manifests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    sectors, manifests = prepare(args.image.read_bytes())
    outputs: list[Path] = []
    for name in sectors:
        outputs.append(args.output_dir / f"{name}.bin")
        outputs.extend(args.output_dir / f"{name}-chunk{index}.bin" for index in range(4))
    outputs.extend(args.output_dir / f"alloc-{allocation}-manifest.json" for allocation in ALLOCATIONS)
    existing = [str(path) for path in outputs if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, sector in sectors.items():
        (args.output_dir / f"{name}.bin").write_bytes(sector)
        for index in range(4):
            (args.output_dir / f"{name}-chunk{index}.bin").write_bytes(sector[index * 0x400 : (index + 1) * 0x400])
    for allocation, manifest in manifests.items():
        manifest["output_dir"] = str(args.output_dir)
        (args.output_dir / f"alloc-{allocation}-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps({"allocations": list(ALLOCATIONS), "output_dir": str(args.output_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
