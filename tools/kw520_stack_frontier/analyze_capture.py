#!/usr/bin/env python3
"""Analyze a fixed KW520 cyclic frontier SRAM/core capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_kw520_stack_frontier as frontier  # noqa: E402


SRAM_BASE = 0x20000000
SRAM_SIZE = 0x4000
BUFFER_ADDRESS = 0x20003978
CORE_RE = re.compile(r"FRONTIER_CORE (?P<fields>.+)")
FIELD_RE = re.compile(r"([a-z]+)=([0-9a-fA-F]{8})")


def pattern_offset(value: int, visible: bytes) -> dict[str, int] | None:
    exact = visible.find(struct.pack("<I", value))
    if exact >= 0:
        return {"offset": exact, "thumb_bit_adjusted": 0}
    adjusted = visible.find(struct.pack("<I", value & ~1))
    if adjusted >= 0:
        return {"offset": adjusted, "thumb_bit_adjusted": value & 1}
    return None


def parse_core(log: str) -> dict[str, int]:
    matches = CORE_RE.findall(log)
    if len(matches) != 1:
        raise ValueError(f"expected one FRONTIER_CORE line, found {len(matches)}")
    fields = {name: int(value, 16) for name, value in FIELD_RE.findall(matches[0])}
    required = {"dhcsr", "icsr", "vtor", "shcsr", "cfsr", "hfsr", "mmfar", "bfar", "msp", "psp", "special", "xpsr", "pc", "lr"}
    if set(fields) != required:
        raise ValueError(f"core field mismatch: {sorted(set(fields) ^ required)}")
    return fields


def sram_word(sram: bytes, address: int) -> int:
    if address < SRAM_BASE or address + 4 > SRAM_BASE + len(sram):
        raise ValueError(f"address outside captured SRAM: 0x{address:08x}")
    return struct.unpack_from("<I", sram, address - SRAM_BASE)[0]


def decode_exception_frame(sram: bytes, core: dict[str, int], visible: bytes | None = None) -> dict[str, object] | None:
    if (core["lr"] & 0xFFFFFF00) != 0xFFFFFF00:
        return None
    stack_name = "psp" if (core["lr"] & 4) else "msp"
    stack_address = core[stack_name]
    if not (SRAM_BASE <= stack_address <= SRAM_BASE + SRAM_SIZE - 32):
        return None
    names = ("r0", "r1", "r2", "r3", "r12", "lr", "pc", "xpsr")
    words = {name: sram_word(sram, stack_address + index * 4) for index, name in enumerate(names)}
    offsets = {}
    if visible is not None:
        offsets = {name: match for name, value in words.items() if (match := pattern_offset(value, visible)) is not None}
    return {
        "stack": stack_name,
        "address": f"0x{stack_address:08x}",
        "words": {name: f"0x{value:08x}" for name, value in words.items()},
        "pattern_offsets": offsets,
    }


def analyze(sram: bytes, log: str, allocation: int) -> dict[str, object]:
    if len(sram) != SRAM_SIZE:
        raise ValueError(f"SRAM capture is {len(sram)} bytes, expected {SRAM_SIZE}")
    visible, payload, _record, _sector = frontier.record_for(allocation)
    core = parse_core(log)
    buffer_offset = BUFFER_ADDRESS - SRAM_BASE
    maximum = min(len(payload), len(sram) - buffer_offset)
    prefix = 0
    while prefix < maximum and sram[buffer_offset + prefix] == payload[prefix]:
        prefix += 1
    occurrences: list[int] = []
    marker = visible[:16]
    cursor = 0
    while True:
        found = sram.find(marker, cursor)
        if found < 0:
            break
        occurrences.append(SRAM_BASE + found)
        cursor = found + 1

    register_offsets = {}
    for name in ("pc", "lr", "msp", "psp", "mmfar", "bfar"):
        match = pattern_offset(core[name], visible)
        if match is not None:
            register_offsets[name] = match

    exception_frame = decode_exception_frame(sram, core, visible)

    end = buffer_offset + allocation
    result: dict[str, object] = {
        "format": 1,
        "allocation": allocation,
        "sram_sha256": hashlib.sha256(sram).hexdigest(),
        "buffer_address": f"0x{BUFFER_ADDRESS:08x}",
        "expected_end_exclusive": f"0x{BUFFER_ADDRESS + allocation:08x}",
        "expected_end_to_msp_bytes": core["msp"] - (BUFFER_ADDRESS + allocation),
        "payload_prefix_bytes": prefix,
        "payload_exact_at_buffer": prefix == len(payload),
        "marker_occurrences": [f"0x{address:08x}" for address in occurrences],
        "bytes_after_expected_end": sram[end : min(end + 32, len(sram))].hex(),
        "core": {name: f"0x{value:08x}" for name, value in core.items()},
        "active_exception": core["xpsr"] & 0x1FF,
        "register_pattern_offsets": register_offsets,
        "exception_frame": exception_frame,
        "control_candidate": bool(register_offsets or (exception_frame and exception_frame["pattern_offsets"])),
    }
    return result


def analyze_baseline(sram: bytes, log: str) -> dict[str, object]:
    if len(sram) != SRAM_SIZE:
        raise ValueError(f"SRAM capture is {len(sram)} bytes, expected {SRAM_SIZE}")
    core = parse_core(log)
    return {
        "format": 1,
        "baseline": True,
        "sram_sha256": hashlib.sha256(sram).hexdigest(),
        "core": {name: f"0x{value:08x}" for name, value in core.items()},
        "active_exception": core["xpsr"] & 0x1FF,
        "exception_frame": decode_exception_frame(sram, core),
        "buffer_to_msp_bytes": core["msp"] - BUFFER_ADDRESS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--allocation", type=int, choices=frontier.ALLOCATIONS)
    mode.add_argument("--baseline", action="store_true")
    parser.add_argument("--sram", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    sram = args.sram.read_bytes()
    log = args.log.read_text(encoding="utf-8", errors="replace")
    result = analyze_baseline(sram, log) if args.baseline else analyze(sram, log, args.allocation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
