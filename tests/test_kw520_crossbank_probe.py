import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_crossbank_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_crossbank_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.POINTER_OFFSET, MODULE.SOURCE_RELATIVE)
    struct.pack_into(">I", image, MODULE.TARGET_POINTER_OFFSET, MODULE.TARGET_RELATIVE)
    struct.pack_into(">H", image, MODULE.SOURCE_RECORD, len(MODULE.SOURCE_PAYLOAD))
    image[MODULE.SOURCE_RECORD + 2 : MODULE.SOURCE_RECORD + 2 + len(MODULE.SOURCE_PAYLOAD)] = MODULE.SOURCE_PAYLOAD
    struct.pack_into(">H", image, MODULE.TARGET_RECORD, len(MODULE.TARGET_PAYLOAD))
    image[MODULE.TARGET_RECORD + 2 : MODULE.TARGET_RECORD + 2 + len(MODULE.TARGET_PAYLOAD)] = MODULE.TARGET_PAYLOAD
    return bytes(image)


def test_prepare_changes_only_crossbank_pointer(monkeypatch):
    image = fixture_image()
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    monkeypatch.setattr(
        MODULE,
        "ORIGINAL_SECTOR_CRC32B",
        MODULE.crc32b(image[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]),
    )
    expected = bytearray(image)
    struct.pack_into(">I", expected, MODULE.POINTER_OFFSET, MODULE.TARGET_RELATIVE)
    monkeypatch.setattr(
        MODULE,
        "PATCHED_SECTOR_CRC32B",
        MODULE.crc32b(expected[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]),
    )

    patched, original_sector, patched_sector, manifest = MODULE.prepare(image)
    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]

    assert changed == [MODULE.POINTER_OFFSET + 2, MODULE.POINTER_OFFSET + 3]
    assert struct.unpack_from(">I", patched, MODULE.POINTER_OFFSET)[0] == MODULE.TARGET_RELATIVE
    assert patched[MODULE.TARGET_RECORD : MODULE.TARGET_RECORD + 2 + len(MODULE.TARGET_PAYLOAD)] == image[MODULE.TARGET_RECORD : MODULE.TARGET_RECORD + 2 + len(MODULE.TARGET_PAYLOAD)]
    assert len(original_sector) == MODULE.SECTOR_SIZE
    assert len(patched_sector) == MODULE.SECTOR_SIZE
    assert manifest["invariants"]["target_is_outside_source_bank"] is True
    assert manifest["expected_observation"]["main_menu_title"] == "Menu principal"


def test_prepare_refuses_unknown_image():
    try:
        MODULE.prepare(fixture_image())
    except ValueError as error:
        assert "unknown base image" in str(error)
    else:
        raise AssertionError("unknown base image was accepted")
