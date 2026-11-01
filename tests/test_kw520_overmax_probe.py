import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_overmax_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_overmax_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.POINTER_OFFSET, MODULE.POINTER_BEFORE)
    return bytes(image)


def test_prepare_changes_only_fixed_pointer_and_new_record(monkeypatch):
    image = fixture_image()
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    pointer_original = image[MODULE.POINTER_SECTOR : MODULE.POINTER_SECTOR + MODULE.SECTOR_SIZE]
    monkeypatch.setattr(MODULE, "POINTER_ORIGINAL_CRC32B", MODULE.crc32b(pointer_original))
    expected_pointer = bytearray(pointer_original)
    struct.pack_into(">I", expected_pointer, MODULE.POINTER_OFFSET - MODULE.POINTER_SECTOR, MODULE.POINTER_AFTER)
    monkeypatch.setattr(MODULE, "POINTER_TEST_CRC32B", MODULE.crc32b(expected_pointer))

    patched, pointer_original, pointer_test, data_original, data_test, manifest = MODULE.prepare(image)
    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    assert changed[:2] == [MODULE.POINTER_OFFSET + 2, MODULE.POINTER_OFFSET + 3]
    assert changed[2:] == list(range(MODULE.DATA_SECTOR, MODULE.DATA_SECTOR + len(MODULE.RECORD)))
    assert pointer_original != pointer_test
    assert data_original == b"\xff" * MODULE.SECTOR_SIZE
    assert data_test[: len(MODULE.RECORD)] == MODULE.RECORD
    assert data_test[len(MODULE.RECORD) :] == b"\xff" * (MODULE.SECTOR_SIZE - len(MODULE.RECORD))
    assert manifest["record"]["allocation"] == 114
    assert manifest["record"]["visible_payload_bytes"] == 113


def test_prepare_refuses_non_ff_data_sector(monkeypatch):
    image = bytearray(fixture_image())
    image[MODULE.DATA_SECTOR + 0x200] = 0
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    monkeypatch.setattr(
        MODULE,
        "POINTER_ORIGINAL_CRC32B",
        MODULE.crc32b(image[MODULE.POINTER_SECTOR : MODULE.POINTER_SECTOR + MODULE.SECTOR_SIZE]),
    )
    try:
        MODULE.prepare(bytes(image))
    except ValueError as error:
        assert "all-FF precondition" in str(error)
    else:
        raise AssertionError("non-FF data sector accepted")
