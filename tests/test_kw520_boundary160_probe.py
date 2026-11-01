import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_boundary160_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_boundary160_probe", MODULE_PATH)
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


def test_prepare_direct_128_to_160_transition(monkeypatch):
    image = fixture_image()
    qualify_fixture(monkeypatch, image)
    _patched, _pointer_original, _pointer_test, previous, test, manifest = MODULE.prepare(image)
    assert previous[: len(MODULE.PREVIOUS_RECORD)] == MODULE.PREVIOUS_RECORD
    assert test[: len(MODULE.RECORD)] == MODULE.RECORD
    assert previous[len(MODULE.PREVIOUS_RECORD) :] == b"\xff" * (MODULE.SECTOR_SIZE - len(MODULE.PREVIOUS_RECORD))
    assert test[len(MODULE.RECORD) :] == b"\xff" * (MODULE.SECTOR_SIZE - len(MODULE.RECORD))
    assert manifest["transition"]["from_crc32b"] == "1f18aa83"
    assert manifest["transition"]["to_crc32b"] == "0c91e3d5"
    assert manifest["record"]["allocation"] == 160
    assert manifest["record"]["visible_payload_bytes"] == 159


def test_fixed_allocation_160_hashes():
    assert MODULE.sha256(MODULE.PAYLOAD) == "cc07b25c0b24fece5cc78767e659bca8209d6f6ecf0b92dcc6836b5ce5a420c5"
    assert MODULE.sha256(MODULE.RECORD) == "67d1e8ea0a507630bb0a0ffc9343883eb195d0eefcfd95d2ddd5d08971f7549c"
    sector = MODULE.RECORD + b"\xff" * (MODULE.SECTOR_SIZE - len(MODULE.RECORD))
    assert MODULE.crc32b(sector) == 0x0C91E3D5
    assert MODULE.sha256(sector) == "4b8c14f8008e650fdfd8cdb679451d4bab2d69898eb43d55ea40c068c28fdfe7"
