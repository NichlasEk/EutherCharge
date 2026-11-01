import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_boundary_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_boundary_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.TITLE_POINTER_OFFSET, MODULE.TITLE_POINTER_BEFORE)
    image[MODULE.NESTED_RECORD : MODULE.NESTED_RECORD + 10] = MODULE.NESTED_ORIGINAL
    return bytes(image)


def test_two_stage_boundary_probe(monkeypatch):
    image = fixture_image()
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    original = image[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]
    monkeypatch.setattr(MODULE, "ORIGINAL_CRC32B", MODULE.crc32b(original))
    baseline_expected = bytearray(image)
    struct.pack_into(">I", baseline_expected, MODULE.TITLE_POINTER_OFFSET, MODULE.NESTED_RELATIVE)
    baseline_expected[MODULE.NESTED_RECORD : MODULE.NESTED_RECORD + 10] = MODULE.BASELINE_RECORD
    monkeypatch.setattr(MODULE, "BASELINE_CRC32B", MODULE.crc32b(baseline_expected[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]))
    extended_expected = bytearray(baseline_expected)
    extended_expected[MODULE.NESTED_RECORD + 1] = 8
    monkeypatch.setattr(MODULE, "EXTENDED_CRC32B", MODULE.crc32b(extended_expected[MODULE.SECTOR_BASE : MODULE.SECTOR_BASE + MODULE.SECTOR_SIZE]))
    baseline_image, extended_image, original_out, baseline, extended, manifest = MODULE.prepare(image)
    assert baseline_image[MODULE.NESTED_RECORD : MODULE.NESTED_RECORD + 10] == MODULE.BASELINE_RECORD
    assert extended_image[MODULE.NESTED_RECORD : MODULE.NESTED_RECORD + 10] == MODULE.EXTENDED_RECORD
    changes = [i for i, pair in enumerate(zip(baseline_image, extended_image)) if pair[0] != pair[1]]
    assert changes == [MODULE.NESTED_RECORD + 1]
    assert len(original_out) == len(baseline) == len(extended) == MODULE.SECTOR_SIZE
    assert manifest["expected_observations"] == {"baseline": "SAFE", "extended": "SAFEWXYZ"}
    assert manifest["safety"]["active_neighbor_record_modified"] is False


def test_refuses_unknown_image():
    try:
        MODULE.prepare(fixture_image())
    except ValueError as error:
        assert "unknown base image" in str(error)
    else:
        raise AssertionError("unknown image was accepted")
