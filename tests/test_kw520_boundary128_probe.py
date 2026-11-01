import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_boundary128_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_boundary128_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture_image() -> bytes:
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    struct.pack_into(">I", image, MODULE.POINTER_OFFSET, MODULE.POINTER_BEFORE)
    return bytes(image)


def qualify_fixture(monkeypatch, image: bytes) -> None:
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())
    pointer_original = image[MODULE.POINTER_SECTOR : MODULE.POINTER_SECTOR + MODULE.SECTOR_SIZE]
    monkeypatch.setattr(MODULE, "POINTER_ORIGINAL_CRC32B", MODULE.crc32b(pointer_original))
    pointer_test = bytearray(pointer_original)
    struct.pack_into(">I", pointer_test, MODULE.POINTER_OFFSET - MODULE.POINTER_SECTOR, MODULE.POINTER_AFTER)
    monkeypatch.setattr(MODULE, "POINTER_TEST_CRC32B", MODULE.crc32b(pointer_test))


def test_prepare_exact_allocation_128_record(monkeypatch):
    image = fixture_image()
    qualify_fixture(monkeypatch, image)
    patched, pointer_original, pointer_test, data_original, data_test, manifest = MODULE.prepare(image)
    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    assert changed[:2] == [MODULE.POINTER_OFFSET + 2, MODULE.POINTER_OFFSET + 3]
    assert changed[2:] == list(range(MODULE.DATA_SECTOR, MODULE.DATA_SECTOR + len(MODULE.RECORD)))
    assert pointer_original != pointer_test
    assert data_original == b"\xff" * MODULE.SECTOR_SIZE
    assert data_test[: len(MODULE.RECORD)] == MODULE.RECORD
    assert data_test[len(MODULE.RECORD) :] == b"\xff" * (MODULE.SECTOR_SIZE - len(MODULE.RECORD))
    assert manifest["record"]["allocation"] == 128
    assert manifest["record"]["visible_payload_bytes"] == 127
    assert MODULE.PAYLOAD[-1] == 0


def test_prepare_refuses_non_ff_data_sector(monkeypatch):
    image = bytearray(fixture_image())
    image[MODULE.DATA_SECTOR + 0x200] = 0
    qualify_fixture(monkeypatch, bytes(image))
    try:
        MODULE.prepare(bytes(image))
    except ValueError as error:
        assert "all-FF precondition" in str(error)
    else:
        raise AssertionError("non-FF data sector accepted")


def test_fixed_payload_and_sector_hashes():
    assert MODULE.sha256(MODULE.PAYLOAD) == "dbfd0a79daaf2ffc18738c27e9ffe941906c096671238c23c4f092c60a586f61"
    assert MODULE.sha256(MODULE.RECORD) == "cf48435053a7bddbd1c3aa9763670788f8b8d4b8237e8f5bfcb92c1e75b7e3c8"
    sector = bytearray(b"\xff" * MODULE.SECTOR_SIZE)
    sector[: len(MODULE.RECORD)] = MODULE.RECORD
    assert MODULE.crc32b(sector) == 0x1F18AA83
    assert MODULE.sha256(sector) == "013758d6704cdab4d96c272a0f3c6749599a0e14a6826aec775867597cc84c16"
