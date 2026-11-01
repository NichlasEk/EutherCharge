import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_maxrecord_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_maxrecord_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.POINTER_OFFSET, MODULE.SOURCE_RELATIVE)
    payload = bytes((index % 251) + 1 for index in range(MODULE.TARGET_ALLOCATION - 1)) + b"\0"
    struct.pack_into(">H", image, MODULE.TARGET_RECORD, len(payload))
    image[MODULE.TARGET_RECORD + 2 : MODULE.TARGET_RECORD + 2 + len(payload)] = payload
    return bytes(image)


def test_prepare_changes_only_title_pointer(monkeypatch):
    image = fixture_image()
    allocation = MODULE.TARGET_ALLOCATION
    record = image[MODULE.TARGET_RECORD : MODULE.TARGET_RECORD + 2 + allocation]
    payload = record[2:]
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    monkeypatch.setattr(MODULE, "TARGET_RECORD_SHA256", hashlib.sha256(record).hexdigest())
    monkeypatch.setattr(MODULE, "TARGET_PAYLOAD_SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(MODULE, "ORIGINAL_CRC32B", MODULE.crc32b(image[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]))
    expected = bytearray(image)
    struct.pack_into(">I", expected, MODULE.POINTER_OFFSET, MODULE.TARGET_RELATIVE)
    monkeypatch.setattr(MODULE, "PATCHED_CRC32B", MODULE.crc32b(expected[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]))

    patched_image, original, patched, manifest = MODULE.prepare(image)
    changed = [index for index, pair in enumerate(zip(image, patched_image)) if pair[0] != pair[1]]
    assert changed == [MODULE.POINTER_OFFSET + 2, MODULE.POINTER_OFFSET + 3]
    assert original != patched
    assert manifest["target"]["allocation"] == 113
    assert manifest["target"]["visible_payload_bytes"] == 112
    assert manifest["invariants"]["length_modified"] is False


def test_prepare_refuses_unknown_image():
    try:
        MODULE.prepare(fixture_image())
    except ValueError as error:
        assert "unknown base image" in str(error)
    else:
        raise AssertionError("unknown image accepted")
