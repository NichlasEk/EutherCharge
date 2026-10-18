#!/usr/bin/env python3
"""Checksum-first helpers for EutherCharge firmware research."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


KNOWN_JEDEC_IDS = {
    "1c3016": {
        "part": "Eon EN25Q32(A/B)",
        "capacity_bytes": 4 * 1024 * 1024,
        "voltage": "2.7-3.6 V",
        "note": "Detected by flashrom; confirm the exact revision from the package marking.",
    },
    "9d0046": {
        "part": "PM25LQ032C",
        "capacity_bytes": 4 * 1024 * 1024,
        "voltage": "2.7-3.6 V",
        "note": "Candidate only; also seen with JEP106 continuation codes.",
    },
    "9d46": {
        "part": "PM25LQ032C / IS25LQ032C",
        "capacity_bytes": 4 * 1024 * 1024,
        "voltage": "3.3 V class",
        "note": "Short-form ID reported by some programmers.",
    },
}


@dataclass(frozen=True)
class Patch:
    offset: int
    expected: bytes
    replacement: bytes


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def printable_strings(data: bytes, minimum: int = 5, limit: int = 25) -> list[dict[str, object]]:
    pattern = re.compile(rb"[\x20-\x7e]{%d,}" % minimum)
    found = []
    for match in pattern.finditer(data):
        found.append({"offset": match.start(), "text": match.group().decode("ascii")})
        if len(found) == limit:
            break
    return found


def edge_runs(data: bytes) -> dict[str, int]:
    result: dict[str, int] = {}
    for value, label in ((0x00, "leading_00"), (0xFF, "leading_ff")):
        count = 0
        for byte in data:
            if byte != value:
                break
            count += 1
        result[label] = count
    for value, label in ((0x00, "trailing_00"), (0xFF, "trailing_ff")):
        count = 0
        for byte in reversed(data):
            if byte != value:
                break
            count += 1
        result[label] = count
    return result


def inspect_file(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": sha256(data),
        "entropy_bits_per_byte": round(entropy(data), 6),
        "byte_values_used": len(set(data)),
        "edge_runs": edge_runs(data),
        "strings": printable_strings(data),
    }


def command_inspect(args: argparse.Namespace) -> int:
    report = inspect_file(args.image)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(f"Path:      {report['path']}")
    print(f"Size:      {report['size_bytes']} bytes")
    print(f"SHA-256:   {report['sha256']}")
    print(f"Entropy:   {report['entropy_bits_per_byte']} bits/byte")
    print(f"Byte vals: {report['byte_values_used']}/256")
    runs = report["edge_runs"]
    assert isinstance(runs, dict)
    print("Edge runs: " + ", ".join(f"{key}={value}" for key, value in runs.items()))
    strings = report["strings"]
    assert isinstance(strings, list)
    if strings:
        print("Strings:")
        for item in strings:
            assert isinstance(item, dict)
            print(f"  0x{int(item['offset']):08x}  {item['text']}")
    return 0


def first_difference(left: bytes, right: bytes) -> int | None:
    for offset, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return offset
    return min(len(left), len(right)) if len(left) != len(right) else None


def command_compare(args: argparse.Namespace) -> int:
    base_path = args.images[0]
    base = base_path.read_bytes()
    base_hash = sha256(base)
    print(f"{base_hash}  {base_path}  ({len(base)} bytes)")
    identical = True
    for path in args.images[1:]:
        data = path.read_bytes()
        digest = sha256(data)
        print(f"{digest}  {path}  ({len(data)} bytes)")
        offset = first_difference(base, data)
        if offset is not None:
            identical = False
            print(f"MISMATCH: first difference versus {base_path} at 0x{offset:x}", file=sys.stderr)
    if identical:
        print(f"OK: {len(args.images)} byte-identical reads")
        return 0
    return 1


def normalize_hex(value: str) -> str:
    return value.lower().replace("0x", "").replace("_", "").replace(" ", "")


def parse_patch(value: str) -> Patch:
    try:
        offset_text, expected_text, replacement_text = value.split(":", 2)
        offset = int(offset_text, 0)
        expected = bytes.fromhex(normalize_hex(expected_text))
        replacement = bytes.fromhex(normalize_hex(replacement_text))
    except (ValueError, TypeError) as error:
        raise argparse.ArgumentTypeError(
            "patch must be OFFSET:EXPECTED_HEX:REPLACEMENT_HEX"
        ) from error
    if offset < 0:
        raise argparse.ArgumentTypeError("offset must not be negative")
    if not expected:
        raise argparse.ArgumentTypeError("expected bytes must not be empty")
    if len(expected) != len(replacement):
        raise argparse.ArgumentTypeError("patch must preserve length")
    return Patch(offset, expected, replacement)


def command_patch(args: argparse.Namespace) -> int:
    source = args.input.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("refusing to overwrite the source image")
    if output.exists() and not args.force:
        raise SystemExit(f"output exists: {output} (use --force to replace it)")

    original = args.input.read_bytes()
    modified = bytearray(original)
    occupied: set[int] = set()
    patch_records = []
    for patch in sorted(args.patch, key=lambda item: item.offset):
        end = patch.offset + len(patch.expected)
        if end > len(original):
            raise SystemExit(f"patch at 0x{patch.offset:x} exceeds image size")
        positions = set(range(patch.offset, end))
        if positions & occupied:
            raise SystemExit(f"overlapping patch at 0x{patch.offset:x}")
        occupied.update(positions)
        actual = original[patch.offset:end]
        if actual != patch.expected:
            raise SystemExit(
                f"guard failed at 0x{patch.offset:x}: "
                f"expected {patch.expected.hex()}, found {actual.hex()}"
            )
        modified[patch.offset:end] = patch.replacement
        patch_records.append(
            {
                "offset": patch.offset,
                "expected_hex": patch.expected.hex(),
                "replacement_hex": patch.replacement.hex(),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(modified)
    manifest_path = args.manifest or Path(str(args.output) + ".manifest.json")
    manifest = {
        "format": 1,
        "source": {"path": str(args.input), "size": len(original), "sha256": sha256(original)},
        "output": {"path": str(args.output), "size": len(modified), "sha256": sha256(modified)},
        "patches": patch_records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({manifest['output']['sha256']})")
    print(f"Manifest: {manifest_path}")
    return 0


def command_identify(args: argparse.Namespace) -> int:
    value = normalize_hex(args.jedec_id)
    try:
        bytes.fromhex(value)
    except ValueError as error:
        raise SystemExit(f"invalid hexadecimal JEDEC ID: {args.jedec_id}") from error
    match = KNOWN_JEDEC_IDS.get(value)
    if not match:
        print(f"Unknown ID: {value}")
        print("Do not guess the part or voltage; consult the programmer output and datasheet.")
        return 1
    print(f"Candidate: {match['part']}")
    print(f"Capacity:  {match['capacity_bytes']} bytes")
    print(f"Supply:    {match['voltage']}")
    print(f"Note:      {match['note']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="summarize a firmware image")
    inspect_parser.add_argument("image", type=Path)
    inspect_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    inspect_parser.set_defaults(func=command_inspect)

    compare_parser = subparsers.add_parser("compare", help="verify two or more reads")
    compare_parser.add_argument("images", nargs="+", type=Path)
    compare_parser.set_defaults(func=command_compare)

    identify_parser = subparsers.add_parser("identify", help="look up a measured JEDEC ID")
    identify_parser.add_argument("jedec_id", help="hex bytes, for example 9d0046")
    identify_parser.set_defaults(func=command_identify)

    patch_parser = subparsers.add_parser("patch", help="create a guarded patched copy")
    patch_parser.add_argument("input", type=Path)
    patch_parser.add_argument("output", type=Path)
    patch_parser.add_argument(
        "--patch",
        action="append",
        required=True,
        type=parse_patch,
        metavar="OFFSET:EXPECTED:REPLACEMENT",
    )
    patch_parser.add_argument("--manifest", type=Path)
    patch_parser.add_argument("--force", action="store_true", help="replace an existing output")
    patch_parser.set_defaults(func=command_patch)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "compare" and len(args.images) < 2:
        parser.error("compare requires at least two images")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
