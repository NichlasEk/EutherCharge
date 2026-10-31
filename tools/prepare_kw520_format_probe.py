#!/usr/bin/env python3
"""Prepare the first bounded KW520 external-flash parser experiment.

The experiment changes only the two bytes ``me`` in the installed Swedish
main-menu title ``Huvudmeny`` to ``%%``.  Both transitions are NOR-safe 1->0
programming operations, so the probe itself needs no sector erase.  The tool
also emits the exact original 4 KiB sector required for later restoration.
It never modifies its input image.
"""

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
PAGE_BASE = 0x003800
PAGE_SIZE = 0x100
PATCH_OFFSET = 0x003899
BEFORE = b"me"
AFTER = b"%%"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc32b(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xffffffff:08x}"


def prepare(image: bytes) -> tuple[bytes, bytes, bytes, dict[str, object]]:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"image is {len(image)} bytes, expected {IMAGE_SIZE}")
    digest = sha256(image)
    if digest != INSTALLED_SHA256:
        raise ValueError(
            "refusing an unknown base image: "
            f"SHA-256 {digest}, expected installed image {INSTALLED_SHA256}"
        )
    if image[PATCH_OFFSET : PATCH_OFFSET + len(BEFORE)] != BEFORE:
        actual = image[PATCH_OFFSET : PATCH_OFFSET + len(BEFORE)].hex()
        raise ValueError(
            f"precondition failed at 0x{PATCH_OFFSET:06x}: {actual} != {BEFORE.hex()}"
        )
    if any((old & new) != new for old, new in zip(BEFORE, AFTER, strict=True)):
        raise AssertionError("probe contains a forbidden 0->1 transition")

    patched = bytearray(image)
    patched[PATCH_OFFSET : PATCH_OFFSET + len(AFTER)] = AFTER
    changed = [index for index, (old, new) in enumerate(zip(image, patched)) if old != new]
    expected = [PATCH_OFFSET, PATCH_OFFSET + 1]
    if changed != expected:
        raise AssertionError(f"unexpected changed offsets: {changed}")

    original_sector = image[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE]
    patched_sector = bytes(patched[SECTOR_BASE : SECTOR_BASE + SECTOR_SIZE])
    patched_page = bytes(patched[PAGE_BASE : PAGE_BASE + PAGE_SIZE])
    manifest: dict[str, object] = {
        "format": 1,
        "operation": "kw520-format-literal-discriminator",
        "source": {
            "size_bytes": len(image),
            "sha256": digest,
        },
        "target": {
            "sector_base": f"0x{SECTOR_BASE:06x}",
            "sector_size": SECTOR_SIZE,
            "page_base": f"0x{PAGE_BASE:06x}",
            "page_size": PAGE_SIZE,
            "patch_offset": f"0x{PATCH_OFFSET:06x}",
            "before_hex": BEFORE.hex(),
            "after_hex": AFTER.hex(),
            "bit_transitions": "1-to-0-only",
            "page_program_bytes_required": len(AFTER),
            "sector_erase_required_for_probe": False,
        },
        "hashes": {
            "original_sector_sha256": sha256(original_sector),
            "original_sector_crc32b": crc32b(original_sector),
            "patched_sector_sha256": sha256(patched_sector),
            "patched_sector_crc32b": crc32b(patched_sector),
            "patched_page_sha256": sha256(patched_page),
            "patched_full_image_sha256": sha256(bytes(patched)),
        },
        "expected_observation": {
            "literal_renderer": "Huvud%%ny",
            "printf_like_renderer": "Huvud%ny",
            "reason": "%% consumes no variadic argument and renders one percent in printf semantics",
        },
        "safety": {
            "source_image_modified": False,
            "only_two_bytes_differ": True,
            "restore_requires_sector_erase": True,
            "write_not_authorized_by_manifest": True,
            "required_before_write": [
                "live sector readback equals original_sector_sha256",
                "JEDEC ID equals 1c3016",
                "fixed-address helper readback equals its build",
                "tested sector-restore helper is available",
            ],
        },
    }
    return bytes(patched), original_sector, patched_page, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="installed 4 MiB EutherCharge readback")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    patched, original_sector, patched_page, manifest = prepare(args.image.read_bytes())
    outputs = {
        "patch_bytes": args.output_dir / "probe-bytes-003899.bin",
        "patched_page": args.output_dir / "probe-page-003800.bin",
        "restore_sector": args.output_dir / "restore-sector-003000.bin",
        "restore_chunk_0": args.output_dir / "restore-sector-003000-chunk0.bin",
        "restore_chunk_1": args.output_dir / "restore-sector-003000-chunk1.bin",
        "restore_chunk_2": args.output_dir / "restore-sector-003000-chunk2.bin",
        "restore_chunk_3": args.output_dir / "restore-sector-003000-chunk3.bin",
        "patched_image": args.output_dir / "format-probe-full.bin",
        "manifest": args.output_dir / "manifest.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise SystemExit("refusing to replace existing output(s): " + ", ".join(existing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["patch_bytes"].write_bytes(AFTER)
    outputs["patched_page"].write_bytes(patched_page)
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
