#!/usr/bin/env python3
"""Validate and assemble one 64 KiB KW520 internal-flash readout."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


CHUNK_COUNT = 64
CHUNK_SIZE = 1024
IMAGE_SIZE = CHUNK_COUNT * CHUNK_SIZE
SRAM_START = 0x20000000
SRAM_END = 0x20004000
FLASH_START = 0x08000000
FLASH_END = FLASH_START + IMAGE_SIZE


def read_chunks(directory: Path) -> bytes:
    chunks: list[bytes] = []
    for index in range(CHUNK_COUNT):
        path = directory / f"chunk-{index:02d}.bin"
        try:
            data = path.read_bytes()
        except FileNotFoundError as error:
            raise SystemExit(f"missing chunk: {path}") from error
        if len(data) != CHUNK_SIZE:
            raise SystemExit(
                f"invalid chunk size: {path} has {len(data)}, expected {CHUNK_SIZE}"
            )
        chunks.append(data)
    image = b"".join(chunks)
    if len(image) != IMAGE_SIZE:
        raise AssertionError("internal image size mismatch")
    return image


def image_report(image: bytes) -> dict[str, object]:
    initial_sp, reset_vector = struct.unpack_from("<II", image)
    return {
        "size": len(image),
        "sha256": hashlib.sha256(image).hexdigest(),
        "initial_sp": f"0x{initial_sp:08x}",
        "reset_vector": f"0x{reset_vector:08x}",
        "initial_sp_plausible": SRAM_START <= initial_sp <= SRAM_END,
        "reset_vector_plausible": (
            bool(reset_vector & 1)
            and FLASH_START <= (reset_vector & ~1) < FLASH_END
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks", type=Path, help="directory containing chunk-00.bin .. chunk-63.bin")
    parser.add_argument("output", type=Path, help="new 64 KiB output image")
    parser.add_argument(
        "--compare",
        type=Path,
        help="require the assembled image to equal this independent readout",
    )
    parser.add_argument(
        "--helper",
        type=Path,
        help="also require helper readback and SRAM restoration evidence",
    )
    parser.add_argument(
        "--allow-implausible-vectors",
        action="store_true",
        help="write a diagnostic image even if its Cortex-M vectors are implausible",
    )
    parser.add_argument(
        "--force", action="store_true", help="allow replacing an existing output file"
    )
    args = parser.parse_args()

    image = read_chunks(args.chunks)
    if args.compare is not None:
        reference = args.compare.read_bytes()
        if len(reference) != IMAGE_SIZE:
            raise SystemExit(
                f"comparison image has {len(reference)} bytes, expected {IMAGE_SIZE}"
            )
        if image != reference:
            raise SystemExit("independent readouts differ; output not written")

    report = image_report(image)
    if not args.allow_implausible_vectors and not (
        report["initial_sp_plausible"] and report["reset_vector_plausible"]
    ):
        raise SystemExit("implausible Cortex-M vector table; output not written")

    if args.helper is not None:
        expected_helper = args.helper.read_bytes()
        helper_readback = (args.chunks / "helper-readback.bin").read_bytes()
        if helper_readback != expected_helper:
            raise SystemExit("SRAM helper readback differs; output not written")
        backup = (args.chunks / "sram-backup.bin").read_bytes()
        restored = (args.chunks / "sram-restored-readback.bin").read_bytes()
        if len(backup) != 0x1400 or restored != backup:
            raise SystemExit("SRAM restoration readback differs; output not written")
        report["helper_sha256"] = hashlib.sha256(helper_readback).hexdigest()
        report["sram_restore_match"] = True

    if args.output.exists() and not args.force:
        raise SystemExit(f"output already exists: {args.output} (use --force to replace)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image)

    report["output"] = str(args.output)
    report["independent_match"] = args.compare is not None
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
