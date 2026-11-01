#!/usr/bin/env python3
"""Find Cortex-M exception-frame-shaped records in retained KW520 SRAM captures.

The protected target enters HardFault/lockup when debug is activated.  A normal
Cortex-M exception frame is eight 32-bit words.  This scanner records only
strictly aligned, frame-shaped candidates whose PC and LR look like addresses
inside the 64 KiB main Flash.  A hit can be an active frame, a stale frame, or
coincidental data; it is evidence for follow-up correlation, not disassembly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


SRAM_BASE = 0x20000000
SRAM_END = 0x20004000
FLASH_BASE = 0x08000000
FLASH_END = 0x08010000
FRAME_WORDS = ("r0", "r1", "r2", "r3", "r12", "lr", "pc", "xpsr")


def is_flash_pc(value: int) -> bool:
    return FLASH_BASE <= value < FLASH_END and value & 1 == 0


def is_flash_lr(value: int) -> bool:
    return FLASH_BASE < value < FLASH_END and value & 1 == 1


def scan_capture(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) != SRAM_END - SRAM_BASE:
        raise ValueError(f"{path}: expected 16384 bytes, got {len(data)}")

    candidates: list[dict[str, object]] = []
    for offset in range(0, len(data) - 31, 4):
        words = struct.unpack_from("<8I", data, offset)
        values = dict(zip(FRAME_WORDS, words, strict=True))
        xpsr = values["xpsr"]
        if not (xpsr & (1 << 24)):
            continue
        if xpsr & 0x1FF > 15:
            continue
        if not is_flash_pc(values["pc"]):
            continue
        if not is_flash_lr(values["lr"]):
            continue
        candidates.append(
            {
                "address": f"0x{SRAM_BASE + offset:08x}",
                "words": {name: f"0x{value:08x}" for name, value in values.items()},
                "ipsr": xpsr & 0x1FF,
            }
        )

    return {
        "capture": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    captures = [scan_capture(path) for path in sorted(set(args.captures))]
    all_candidates = [
        {"capture": item["capture"], **candidate}
        for item in captures
        for candidate in item["candidates"]
    ]
    lr_histogram: dict[str, int] = {}
    for candidate in all_candidates:
        lr = candidate["words"]["lr"]
        lr_histogram[lr] = lr_histogram.get(lr, 0) + 1

    result = {
        "format": 1,
        "method": "aligned Cortex-M basic exception-frame shape scan",
        "limits": [
            "Candidates can be active frames, stale stack frames, or coincidental data.",
            "No candidate contains instruction bytes or proves that its PC is a callable function entry.",
            "Raw SRAM remains local and ignored.",
        ],
        "capture_count": len(captures),
        "candidate_count": len(all_candidates),
        "captures": captures,
        "lr_histogram": dict(sorted(lr_histogram.items())),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
