import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_stack_frontier.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_stack_frontier", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.POINTER_OFFSET, MODULE.POINTER_BEFORE)
    return bytes(image)


def qualify_fixture(monkeypatch, image: bytes) -> None:
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    pointer = image[MODULE.POINTER_SECTOR : MODULE.POINTER_SECTOR + MODULE.SECTOR_SIZE]
    monkeypatch.setattr(MODULE, "POINTER_ORIGINAL_CRC32B", MODULE.crc32b(pointer))
    test = bytearray(pointer)
    struct.pack_into(">I", test, MODULE.POINTER_OFFSET - MODULE.POINTER_SECTOR, MODULE.POINTER_AFTER)
    monkeypatch.setattr(MODULE, "POINTER_TEST_CRC32B", MODULE.crc32b(test))


def test_all_fixed_profiles_have_unique_safe_cyclic_payloads(monkeypatch):
    image = fixture_image()
    qualify_fixture(monkeypatch, image)
    sectors, manifests = MODULE.prepare(image)
    hashes = set()
    for allocation in MODULE.ALLOCATIONS:
        visible, payload, record, sector = MODULE.record_for(allocation)
        assert len(visible) == allocation - 1
        assert len(payload) == allocation and payload[-1] == 0
        assert len(record) == allocation + 2 and len(sector) == 0x1000
        assert b"%" not in visible and b"\0" not in visible
        assert manifests[allocation]["record"]["expected_end_exclusive"] == f"0x{0x20003978 + allocation:08x}"
        hashes.add(hashlib.sha256(sectors[f"alloc-{allocation}-data-test-sector-00c000"]).digest())
    assert len(hashes) == len(MODULE.ALLOCATIONS)


def test_refuses_every_unqualified_allocation():
    for allocation in (0, 240, 255, 257, 544, 4094):
        try:
            MODULE.record_for(allocation)
        except ValueError as error:
            assert "outside fixed stack-frontier" in str(error)
        else:
            raise AssertionError(f"unsafe allocation accepted: {allocation}")


def test_cyclic_four_byte_windows_are_unique_through_512():
    pattern = MODULE.cyclic(511)
    windows = [pattern[index : index + 4] for index in range(len(pattern) - 3)]
    assert len(windows) == len(set(windows))
    words = [struct.unpack("<I", window)[0] for window in windows]
    assert not any(0x08000000 <= word < 0x08010000 for word in words)
    assert not any(0x20000000 <= word < 0x20004000 for word in words)
    assert not any(0x40000000 <= word < 0x60000000 for word in words)
