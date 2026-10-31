#!/usr/bin/env python3
"""Reproducible, read-only structural audit of a KW520 EN25Q32 dump."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import struct
from pathlib import Path


SECTOR = 0x1000
EXPECTED_SIZE = 0x400000
EXPECTED_SHA256 = "d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2"
POINTER_BASE = 0x3200
BANK_TABLES = (0x3600, 0x4356, 0x546D, 0x6443, 0x7415, 0x843F, 0x9414, 0xA3F2)
ENTRY_COUNT = 162

MAGICS = {
    "gzip": bytes.fromhex("1f8b08"),
    "xz": bytes.fromhex("fd377a585a00"),
    "zip": b"PK\x03\x04",
    "7z": bytes.fromhex("377abcaf271c"),
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": bytes.fromhex("ffd8ff"),
    "bmp": b"BM",
    "elf": b"\x7fELF",
    "uf2": bytes.fromhex("5546320a"),
    "lz4_frame": bytes.fromhex("04224d18"),
    "squashfs_le": b"hsqs",
    "squashfs_be": b"sqsh",
}


def entropy(block: bytes) -> float:
    if not block:
        return 0.0
    counts = collections.Counter(block)
    return -sum((count / len(block)) * math.log2(count / len(block)) for count in counts.values())


def ranges(values: list[int], step: int) -> list[list[int]]:
    if not values:
        return []
    out: list[list[int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + step:
            out.append([start, previous + step])
            start = value
        previous = value
    out.append([start, previous + step])
    return out


def non_fill_runs(data: bytes, start: int, end: int, fill: int = 0xFF) -> list[dict[str, int]]:
    found: list[dict[str, int]] = []
    pos = start
    while pos < end:
        while pos < end and data[pos] == fill:
            pos += 1
        run_start = pos
        while pos < end and data[pos] != fill:
            pos += 1
        if run_start < pos:
            found.append({"start": run_start, "end": pos, "length": pos - run_start})
    return found


def ascii_strings(data: bytes, minimum: int = 4) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    pos = 0
    while pos < len(data):
        if 0x20 <= data[pos] <= 0x7E:
            start = pos
            while pos < len(data) and 0x20 <= data[pos] <= 0x7E:
                pos += 1
            if pos - start >= minimum:
                found.append({"offset": start, "length": pos - start, "text": data[start:pos].decode("ascii")})
        else:
            pos += 1
    return found


def monotonic_word_runs(data: bytes, endian: str, minimum: int = 8) -> list[dict[str, object]]:
    """Find dense unaligned runs of increasing plausible 32-bit offsets."""
    fmt = ">I" if endian == "big" else "<I"
    candidates: list[dict[str, object]] = []
    for phase in range(4):
        pos = phase
        while pos + 4 <= len(data):
            first = struct.unpack_from(fmt, data, pos)[0]
            if not (1 <= first < 0x400000):
                pos += 4
                continue
            vals = [first]
            cursor = pos + 4
            while cursor + 4 <= len(data):
                value = struct.unpack_from(fmt, data, cursor)[0]
                delta = value - vals[-1]
                if not (1 <= delta <= 0x1000 and value < 0x400000):
                    break
                vals.append(value)
                cursor += 4
            if len(vals) >= minimum:
                candidates.append({
                    "offset": pos,
                    "endian": endian,
                    "count": len(vals),
                    "first": vals[0],
                    "last": vals[-1],
                    "min_step": min(b - a for a, b in zip(vals, vals[1:])),
                    "max_step": max(b - a for a, b in zip(vals, vals[1:])),
                })
                pos = cursor
            else:
                pos += 4
    return candidates


def repeated_blocks(data: bytes, block_size: int, allowed_sector_offsets: set[int]) -> list[dict[str, object]]:
    index: dict[bytes, list[int]] = collections.defaultdict(list)
    for offset in sorted(allowed_sector_offsets):
        sector = data[offset:offset + SECTOR]
        for inner in range(0, SECTOR, block_size):
            block = sector[inner:inner + block_size]
            if block in (bytes(block_size), bytes([0xFF]) * block_size):
                continue
            index[hashlib.sha256(block).digest()].append(offset + inner)
    groups = [
        {"length": block_size, "offsets": offsets}
        for offsets in index.values() if len(offsets) > 1
    ]
    groups.sort(key=lambda item: (-len(item["offsets"]), item["offsets"][0]))
    return groups[:100]


def parse_known_tables(data: bytes) -> list[dict[str, object]]:
    tables: list[dict[str, object]] = []
    for table in BANK_TABLES:
        values = [struct.unpack_from(">I", data, table + index * 4)[0] for index in range(ENTRY_COUNT)]
        absolute = [POINTER_BASE + value for value in values]
        lengths = [struct.unpack_from(">H", data, offset)[0] for offset in absolute]
        tables.append({
            "table_offset": table,
            "entries": len(values),
            "first_relative": values[0],
            "last_relative": values[-1],
            "strictly_increasing": all(a < b for a, b in zip(values, values[1:])),
            "record_gap_matches_previous_allocation": all(
                absolute[index + 1] - absolute[index] == 2 + lengths[index]
                for index in range(len(absolute) - 1)
            ),
            "allocation_min": min(lengths),
            "allocation_max": max(lengths),
        })
    return tables


def parse_language_directory(data: bytes) -> dict[str, object]:
    """Decode the sparse 19-byte slot directory beginning at 0x3200."""
    declared_count = data[0x3200]
    slots: list[dict[str, object]] = []
    for slot in range(15):
        offset = 0x3201 + slot * 19
        raw = data[offset:offset + 19]
        if raw == bytes([0xFF]) * 19:
            continue
        language_id, table1, count1, table2, count2, table3, count3 = struct.unpack(">BIHIHIH", raw)
        class2_absolute = POINTER_BASE + table2
        class2_entries: list[dict[str, object]] = []
        for index in range(count2):
            entry = class2_absolute + index * 7
            code = int.from_bytes(data[entry:entry + 3], "big")
            string_relative = struct.unpack_from(">I", data, entry + 3)[0]
            string_absolute = POINTER_BASE + string_relative
            allocation = struct.unpack_from(">H", data, string_absolute)[0]
            raw_text = data[string_absolute + 2:string_absolute + 2 + allocation]
            class2_entries.append({
                "code_u24": code,
                "string_relative": string_relative,
                "string_absolute": string_absolute,
                "allocation": allocation,
                "nul_terminated": bool(raw_text) and raw_text[-1] == 0,
                "text_latin1": raw_text.rstrip(b"\0").decode("latin-1"),
            })
        slots.append({
            "slot": slot,
            "slot_offset": offset,
            "language_id": language_id,
            "slot_matches_language_id": slot == language_id,
            "classes": [
                {"relative_table": table1, "absolute_table": POINTER_BASE + table1, "count": count1},
                {
                    "relative_table": table2,
                    "absolute_table": class2_absolute,
                    "count": count2,
                    "entry_width": 7,
                    "entries": class2_entries,
                },
                {"relative_table": table3, "absolute_table": POINTER_BASE + table3, "count": count3},
            ],
        })
    return {
        "offset": 0x3200,
        "declared_active_count": declared_count,
        "decoded_active_count": len(slots),
        "count_matches": declared_count == len(slots),
        "slots": slots,
    }


def crc8_sae_j1850(data: bytes) -> int:
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1D) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc ^ 0xFF


def find_crc_records(data: bytes) -> list[dict[str, object]]:
    """Find A5 records whose first byte validates as CRC-8/SAE-J1850."""
    records: list[dict[str, object]] = []
    for marker in range(1, len(data)):
        if data[marker] != 0xA5:
            continue
        offset = marker - 1
        matches = [
            length for length in range(3, min(256, len(data) - offset) + 1)
            if crc8_sae_j1850(data[offset + 1:offset + length]) == data[offset]
        ]
        if matches:
            records.append({
                "offset": offset,
                "stored_crc": data[offset],
                "candidate_lengths": matches,
                "shortest_length": matches[0],
            })
    return records


def validate_relative_string_tables(data: bytes, candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    validated: list[dict[str, object]] = []
    for candidate in candidates:
        if candidate["endian"] != "big":
            continue
        offset = int(candidate["offset"])
        count = int(candidate["count"])
        good = 0
        for index in range(count):
            relative = struct.unpack_from(">I", data, offset + index * 4)[0]
            record = POINTER_BASE + relative
            if record + 2 > len(data):
                break
            allocation = struct.unpack_from(">H", data, record)[0]
            if allocation < 1 or record + 2 + allocation > len(data):
                break
            if data[record + 1 + allocation] != 0:
                break
            good += 1
        if good == count:
            validated.append({**candidate, "validated_length_prefixed_nul_records": good})
    return validated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    data = args.image.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    sectors: list[dict[str, object]] = []
    non_erased_offsets: set[int] = set()
    for offset in range(0, len(data), SECTOR):
        block = data[offset:offset + SECTOR]
        non_ff = sum(value != 0xFF for value in block)
        non_zero = sum(value != 0 for value in block)
        if non_ff:
            non_erased_offsets.add(offset)
            sectors.append({
                "offset": offset,
                "non_ff": non_ff,
                "non_zero": non_zero,
                "unique_bytes": len(set(block)),
                "entropy": round(entropy(block), 6),
                "sha256": hashlib.sha256(block).hexdigest(),
            })

    magic_hits: list[dict[str, object]] = []
    for name, magic in MAGICS.items():
        start = 0
        while True:
            offset = data.find(magic, start)
            if offset < 0:
                break
            magic_hits.append({"type": name, "offset": offset})
            start = offset + 1

    sector_hash_groups: dict[str, list[int]] = collections.defaultdict(list)
    for item in sectors:
        sector_hash_groups[str(item["sha256"])].append(int(item["offset"]))
    duplicate_sectors = [
        {"offsets": offsets, "count": len(offsets)}
        for offsets in sector_hash_groups.values() if len(offsets) > 1
    ]

    monotonic_candidates = monotonic_word_runs(data, "big") + monotonic_word_runs(data, "little")
    report = {
        "image": str(args.image),
        "size": len(data),
        "expected_size": EXPECTED_SIZE,
        "sha256": digest,
        "expected_sha256": EXPECTED_SHA256,
        "reference_match": len(data) == EXPECTED_SIZE and digest == EXPECTED_SHA256,
        "non_erased_sector_count": len(sectors),
        "non_erased_sector_ranges": ranges(sorted(non_erased_offsets), SECTOR),
        "non_erased_sectors": sectors,
        "non_ff_runs_known_regions": {
            "configuration_0000_35ff": non_fill_runs(data, 0, 0x3600),
            "metadata_380000_382000": non_fill_runs(data, 0x380000, 0x382000),
            "history_383000_384000": non_fill_runs(data, 0x383000, 0x384000),
        },
        "known_language_tables": parse_known_tables(data),
        "language_directory": parse_language_directory(data),
        "monotonic_32bit_offset_candidates": monotonic_candidates,
        "validated_relative_string_tables": validate_relative_string_tables(data, monotonic_candidates),
        "crc8_sae_j1850_a5_records": find_crc_records(data),
        "duplicate_non_erased_sectors": duplicate_sectors,
        "repeated_16byte_blocks": repeated_blocks(data, 16, non_erased_offsets),
        "repeated_32byte_blocks": repeated_blocks(data, 32, non_erased_offsets),
        "magic_hits": sorted(magic_hits, key=lambda item: int(item["offset"])),
        "ascii_strings": ascii_strings(data),
        "special_checks": {
            "sector_001000_equals_002000": data[0x1000:0x2000] == data[0x2000:0x3000],
            "crc32_table_polynomial_le_present": data.find(bytes.fromhex("00000000963007772c610eeeba510999")),
            "cortex_m_vector_candidates": [],
        },
    }

    for offset in range(0, len(data) - 8, 4):
        stack, reset = struct.unpack_from("<II", data, offset)
        if 0x20000000 <= stack <= 0x20004000 and 0x08000001 <= reset <= 0x08010001 and reset & 1:
            report["special_checks"]["cortex_m_vector_candidates"].append({
                "offset": offset, "stack": stack, "reset": reset,
            })

    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["reference_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
