from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "kw520_resources", ROOT / "tools" / "kw520_resources.py"
)
assert SPEC and SPEC.loader
resources = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = resources
SPEC.loader.exec_module(resources)


def synthetic_bank() -> tuple[bytearray, object]:
    bank = resources.BankLayout("Test", 0x1000, 0x3400)
    data = bytearray(b"\xff" * 0x8000)
    cursor = bank.strings_offset
    for index in range(resources.ENTRY_COUNT):
        struct.pack_into(">I", data, bank.table_offset + index * 4, cursor - resources.POINTER_BASE)
        payload = f"E{index}".encode("latin-1") + b"\0"
        struct.pack_into(">H", data, cursor, len(payload))
        data[cursor + 2 : cursor + 2 + len(payload)] = payload
        cursor += 2 + len(payload)
    return data, bank


class ResourceTests(unittest.TestCase):
    def test_parses_pointer_table_and_records(self) -> None:
        data, bank = synthetic_bank()
        entries = resources.parse_bank(data, bank)
        self.assertEqual(len(entries), 162)
        self.assertEqual(entries[0].text, "E0")
        self.assertEqual(entries[161].text, "E161")

    def test_patch_preserves_prefix_allocation_and_size(self) -> None:
        data, bank = synthetic_bank()
        entry = resources.parse_bank(data, bank)[100]
        before_size = len(data)
        before_prefix = bytes(data[entry.record_offset : entry.record_offset + 2])
        resources.BANKS = (bank,)
        resources.patch_entry(data, entry, "X")
        self.assertEqual(len(data), before_size)
        self.assertEqual(data[entry.record_offset : entry.record_offset + 2], before_prefix)
        self.assertEqual(data[entry.record_offset + 2 : entry.record_offset + 7], b"X\0\0\0\0")

    def test_patch_rejects_overflow(self) -> None:
        data, bank = synthetic_bank()
        entry = resources.parse_bank(data, bank)[0]
        resources.BANKS = (bank,)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            resources.patch_entry(data, entry, "TOO-LONG")


if __name__ == "__main__":
    unittest.main()
