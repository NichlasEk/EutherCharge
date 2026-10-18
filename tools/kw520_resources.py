#!/usr/bin/env python3
"""Parse and safely patch known KW520 1.0.1 external-flash resources.

The tool deliberately implements only structures that have been verified against
the three identical TL866A reads. It never overwrites its input image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


KNOWN_IMAGE_SIZE = 4 * 1024 * 1024
KNOWN_SHA256 = "d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2"
POINTER_BASE = 0x3200
ENTRY_COUNT = 162
HISTORY_OFFSET = 0x383000
HISTORY_RECORD_SIZE = 52
HISTORY_MAX_RECORDS = 64


@dataclass(frozen=True)
class BankLayout:
    name: str
    table_offset: int
    strings_offset: int
    encoding: str = "latin-1"
    verified_text: bool = True


BANKS = (
    BankLayout("English", 0x3600, 0x3888),
    BankLayout("Français", 0x4356, 0x45DE),
    BankLayout("Español", 0x546D, 0x56F5),
    BankLayout("Deutsch", 0x6443, 0x66CB),
    BankLayout("Russian-custom", 0x7415, 0x769D, verified_text=False),
    BankLayout("Italiano", 0x843F, 0x86C7),
    BankLayout("Português", 0x9414, 0x969C),
    BankLayout("Nederlands", 0xA3F2, 0xA67A),
)


@dataclass(frozen=True)
class StringEntry:
    language: str
    index: int
    pointer_offset: int
    record_offset: int
    allocation: int
    raw: bytes
    text: str


@dataclass(frozen=True)
class HistoryRecord:
    """Read-only candidate interpretation of one persistent 52-byte record."""

    index: int
    offset: int
    marker_hex: str
    mode_byte_candidate: int
    rated_value: int
    measured_value: int
    voltage_raw: int
    voltage_candidate: float
    health_percent_candidate: int
    charge_percent_candidate: int
    resistance_candidate: float


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_bank(name: str) -> BankLayout:
    folded = name.casefold()
    for bank in BANKS:
        if bank.name.casefold() == folded:
            return bank
    choices = ", ".join(bank.name for bank in BANKS)
    raise ValueError(f"unknown language {name!r}; choose one of: {choices}")


def parse_bank(data: bytes, bank: BankLayout) -> list[StringEntry]:
    entries: list[StringEntry] = []
    previous = -1
    for index in range(ENTRY_COUNT):
        pointer_offset = bank.table_offset + index * 4
        if pointer_offset + 4 > len(data):
            raise ValueError(f"{bank.name}: pointer table exceeds image")
        relative = struct.unpack_from(">I", data, pointer_offset)[0]
        record_offset = POINTER_BASE + relative
        if record_offset < bank.strings_offset or record_offset <= previous:
            raise ValueError(
                f"{bank.name}: invalid pointer #{index} -> 0x{record_offset:x}"
            )
        if record_offset + 2 > len(data):
            raise ValueError(f"{bank.name}: record #{index} exceeds image")
        allocation = struct.unpack_from(">H", data, record_offset)[0]
        content_start = record_offset + 2
        content_end = content_start + allocation
        if allocation < 1 or allocation > 256 or content_end > len(data):
            raise ValueError(
                f"{bank.name}: invalid allocation {allocation} for entry #{index}"
            )
        raw = data[content_start:content_end]
        if raw[-1] != 0:
            raise ValueError(f"{bank.name}: entry #{index} is not NUL-terminated")
        visible = raw[:-1].split(b"\0", 1)[0]
        entries.append(
            StringEntry(
                language=bank.name,
                index=index,
                pointer_offset=pointer_offset,
                record_offset=record_offset,
                allocation=allocation,
                raw=visible,
                text=visible.decode(bank.encoding),
            )
        )
        previous = record_offset
    return entries


def validate_layout(data: bytes) -> dict[str, object]:
    banks = []
    for bank in BANKS:
        entries = parse_bank(data, bank)
        banks.append(
            {
                "name": bank.name,
                "table_offset": bank.table_offset,
                "strings_offset": bank.strings_offset,
                "entries": len(entries),
                "text_decoding_verified": bank.verified_text,
            }
        )
    return {
        "size": len(data),
        "sha256": sha256(data),
        "known_reference": len(data) == KNOWN_IMAGE_SIZE and sha256(data) == KNOWN_SHA256,
        "pointer_base": POINTER_BASE,
        "banks": banks,
    }


def parse_history(data: bytes) -> list[HistoryRecord]:
    """Parse structurally known records without claiming field semantics.

    The A5 marker, 52-byte stride and record count are observed facts. Field
    names ending in ``candidate`` are hypotheses pending comparison with the
    charger's Review screen.
    """

    records: list[HistoryRecord] = []
    for index in range(HISTORY_MAX_RECORDS):
        offset = HISTORY_OFFSET + index * HISTORY_RECORD_SIZE
        if offset + HISTORY_RECORD_SIZE > len(data):
            break
        if data[offset : offset + 2] == b"\xff\xff":
            break
        if data[offset + 1] != 0xA5:
            raise ValueError(f"history record #{index} lacks A5 marker")
        records.append(
            HistoryRecord(
                index=index,
                offset=offset,
                marker_hex=data[offset : offset + 2].hex(),
                mode_byte_candidate=data[offset + 15],
                rated_value=struct.unpack_from("<H", data, offset + 24)[0],
                measured_value=struct.unpack_from("<H", data, offset + 34)[0],
                voltage_raw=struct.unpack_from("<H", data, offset + 36)[0],
                voltage_candidate=struct.unpack_from("<H", data, offset + 36)[0] / 100,
                health_percent_candidate=struct.unpack_from("<H", data, offset + 38)[0],
                charge_percent_candidate=struct.unpack_from("<H", data, offset + 40)[0],
                resistance_candidate=struct.unpack_from("<f", data, offset + 44)[0],
            )
        )
    return records


def patch_entry(image: bytearray, entry: StringEntry, text: str) -> dict[str, object]:
    bank = get_bank(entry.language)
    if not bank.verified_text:
        raise ValueError(
            f"{bank.name} uses an unresolved custom character encoding and is read-only"
        )
    encoded = text.encode(bank.encoding)
    capacity = entry.allocation - 1
    if len(encoded) > capacity:
        raise ValueError(
            f"{bank.name} entry #{entry.index}: {len(encoded)} bytes exceeds "
            f"the fixed {capacity}-byte allocation"
        )
    start = entry.record_offset + 2
    before = bytes(image[start : start + entry.allocation])
    # Keep the record allocation intact but terminate the replacement at once.
    # Remaining bytes are zero-filled so both NUL-based and fixed-count readers
    # see an empty tail rather than visible padding.
    after = encoded + b"\0" * (entry.allocation - len(encoded))
    image[start : start + entry.allocation] = after
    return {
        "language": entry.language,
        "index": entry.index,
        "offset": start,
        "allocation": entry.allocation,
        "before_hex": before.hex(),
        "after_hex": after.hex(),
        "before_text": entry.text,
        "after_text": text,
    }


def parse_set(value: str) -> tuple[str, int, str]:
    try:
        language, index_text, text = value.split(":", 2)
        index = int(index_text, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError("set must be LANGUAGE:INDEX:TEXT") from error
    if not 0 <= index < ENTRY_COUNT:
        raise argparse.ArgumentTypeError(f"entry index must be 0..{ENTRY_COUNT - 1}")
    return language, index, text


def command_scan(args: argparse.Namespace) -> int:
    data = args.image.read_bytes()
    report = validate_layout(data)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def command_strings(args: argparse.Namespace) -> int:
    data = args.image.read_bytes()
    bank = get_bank(args.language)
    entries = parse_bank(data, bank)
    output = [
        {
            "index": item.index,
            "record_offset": item.record_offset,
            "allocation": item.allocation,
            "text": item.text,
        }
        for item in entries
    ]
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def command_history(args: argparse.Namespace) -> int:
    data = args.image.read_bytes()
    records = parse_history(data)
    output = {
        "status": "field-hypotheses-not-physically-correlated",
        "offset": HISTORY_OFFSET,
        "record_size": HISTORY_RECORD_SIZE,
        "records": [record.__dict__ for record in records],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def command_patch_text(args: argparse.Namespace) -> int:
    source = args.input.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("refusing to overwrite the source image")
    if output.exists() and not args.force:
        raise SystemExit(f"output exists: {output} (use --force to replace it)")
    original = args.input.read_bytes()
    validate_layout(original)
    modified = bytearray(original)
    changes = []
    touched: set[tuple[str, int]] = set()
    for language, index, text in args.set:
        bank = get_bank(language)
        key = (bank.name, index)
        if key in touched:
            raise SystemExit(f"duplicate patch for {bank.name} entry #{index}")
        touched.add(key)
        entry = parse_bank(original, bank)[index]
        try:
            changes.append(patch_entry(modified, entry, text))
        except (UnicodeEncodeError, ValueError) as error:
            raise SystemExit(str(error)) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(modified)
    manifest_path = args.manifest or Path(str(args.output) + ".manifest.json")
    manifest = {
        "format": 1,
        "operation": "kw520-fixed-allocation-text-patch",
        "source": {"path": str(args.input), "size": len(original), "sha256": sha256(original)},
        "output": {"path": str(args.output), "size": len(modified), "sha256": sha256(modified)},
        "invariants": {
            "image_size_preserved": len(original) == len(modified),
            "pointer_tables_modified": False,
            "length_prefixes_modified": False,
            "scope": "string payload bytes only",
        },
        "changes": changes,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({manifest['output']['sha256']})")
    print(f"Manifest: {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="validate and describe all known language banks")
    scan.add_argument("image", type=Path)
    scan.set_defaults(func=command_scan)
    strings = commands.add_parser("strings", help="extract one language bank as JSON")
    strings.add_argument("image", type=Path)
    strings.add_argument("--language", default="English")
    strings.set_defaults(func=command_strings)
    history = commands.add_parser(
        "history", help="show read-only 52-byte history records and candidate fields"
    )
    history.add_argument("image", type=Path)
    history.set_defaults(func=command_history)
    patch = commands.add_parser("patch-text", help="create a fixed-allocation text-patched copy")
    patch.add_argument("input", type=Path)
    patch.add_argument("output", type=Path)
    patch.add_argument("--set", action="append", required=True, type=parse_set, metavar="LANGUAGE:INDEX:TEXT")
    patch.add_argument("--manifest", type=Path)
    patch.add_argument("--force", action="store_true")
    patch.set_defaults(func=command_patch_text)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
