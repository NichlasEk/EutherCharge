import hashlib
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "prepare_kw520_format_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_format_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_prepare_changes_only_two_nor_safe_bytes(monkeypatch):
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    image[MODULE.PATCH_OFFSET : MODULE.PATCH_OFFSET + 2] = MODULE.BEFORE
    monkeypatch.setattr(MODULE, "INSTALLED_SHA256", hashlib.sha256(image).hexdigest())

    patched, restore_sector, patched_page, manifest = MODULE.prepare(bytes(image))

    changed = [index for index, pair in enumerate(zip(image, patched)) if pair[0] != pair[1]]
    assert changed == [MODULE.PATCH_OFFSET, MODULE.PATCH_OFFSET + 1]
    assert patched[MODULE.PATCH_OFFSET : MODULE.PATCH_OFFSET + 2] == b"%%"
    assert all((old & new) == new for old, new in zip(MODULE.BEFORE, MODULE.AFTER))
    assert len(restore_sector) == MODULE.SECTOR_SIZE
    assert len(patched_page) == MODULE.PAGE_SIZE
    assert manifest["expected_observation"]["literal_renderer"] == "Huvud%%ny"
    assert manifest["expected_observation"]["printf_like_renderer"] == "Huvud%ny"


def test_prepare_refuses_unknown_image():
    image = bytearray(b"\xff" * MODULE.IMAGE_SIZE)
    image[MODULE.PATCH_OFFSET : MODULE.PATCH_OFFSET + 2] = MODULE.BEFORE
    try:
        MODULE.prepare(bytes(image))
    except ValueError as error:
        assert "unknown base image" in str(error)
    else:
        raise AssertionError("unknown base image was accepted")
