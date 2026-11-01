import hashlib
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_length_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_length_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    image[MODULE.LENGTH_OFFSET : MODULE.LENGTH_OFFSET + 2] = MODULE.BEFORE
    image[MODULE.PAYLOAD_OFFSET : MODULE.PAYLOAD_OFFSET + len(MODULE.PAYLOAD)] = MODULE.PAYLOAD
    return bytes(image)


def test_prepare_only_shortens_length(monkeypatch):
    image = fixture_image()
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    monkeypatch.setattr(
        MODULE,
        "ORIGINAL_SECTOR_CRC32B",
        MODULE.crc32b(image[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]),
    )
    expected = bytearray(image)
    expected[MODULE.LENGTH_OFFSET : MODULE.LENGTH_OFFSET + 2] = MODULE.AFTER
    monkeypatch.setattr(
        MODULE,
        "PATCHED_SECTOR_CRC32B",
        MODULE.crc32b(expected[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]),
    )
    patched, original_sector, patched_sector, manifest = MODULE.prepare(image)
    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    assert changed == [MODULE.LENGTH_OFFSET + 1]
    assert patched[MODULE.PAYLOAD_OFFSET : MODULE.PAYLOAD_OFFSET + len(MODULE.PAYLOAD)] == MODULE.PAYLOAD
    assert all((old & new) == new for old, new in zip(MODULE.BEFORE, MODULE.AFTER))
    assert len(original_sector) == MODULE.SECTOR_SIZE
    assert len(patched_sector) == MODULE.SECTOR_SIZE
    assert manifest["safety"]["copy_length_only_decreases"] is True
    assert manifest["target"]["sector_erase_required_for_probe"] is False


def test_prepare_refuses_unknown_image():
    try:
        MODULE.prepare(fixture_image())
    except ValueError as error:
        assert "unknown base image" in str(error)
    else:
        raise AssertionError("unknown base image was accepted")
