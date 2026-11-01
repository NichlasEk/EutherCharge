import hashlib
import importlib.util
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_boundary_transition.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_boundary_transition", MODULE_PATH)
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


def test_fixed_profiles_and_adjacent_transitions(monkeypatch):
    image = fixture_image()
    qualify_fixture(monkeypatch, image)
    for source, target in sorted(MODULE.ALLOWED_TRANSITIONS):
        sectors, manifest = MODULE.prepare(image, source, target)
        assert MODULE.crc32b(sectors["data-previous"]) == MODULE.FIXED[source]["crc32b"]
        assert MODULE.crc32b(sectors["data-test"]) == MODULE.FIXED[target]["crc32b"]
        assert sectors["data-original"] == b"\xff" * MODULE.SECTOR_SIZE
        assert manifest["record"]["allocation"] == target
        assert manifest["record"]["visible_payload_bytes"] == target - 1


def test_refuses_skipped_or_reverse_transition(monkeypatch):
    image = fixture_image()
    qualify_fixture(monkeypatch, image)
    for edge in ((160, 224), (192, 160), (240, 256)):
        try:
            MODULE.prepare(image, *edge)
        except ValueError as error:
            assert "outside fixed adjacent" in str(error)
        else:
            raise AssertionError(f"unsafe transition accepted: {edge}")
