import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_language_gate.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_language_gate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
IMAGE = ROOT / "dumps" / "readback" / "kw520-after-euthercharge-2026-10-18.bin"


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_language9_probe_is_exact_and_fully_valid():
    original, probe, manifest = MODULE.prepare(IMAGE.read_bytes())
    assert len(original) == len(probe) == 0x1000
    assert MODULE.crc32(original) == 0xF5C23372
    assert MODULE.crc32(probe) == 0xFA2D76BB
    assert manifest["directory"]["active_ids_after"] == [3, 4, 5, 6, 7, 8, 9, 10, 14]
    assert manifest["directory"]["test_entry"] == {
        "language_id": 9,
        "ordinary_table_relative": 0x523F,
        "ordinary_count": 162,
        "dtc_table_relative": 0x81BF,
        "dtc_count": 1,
        "third_table_relative": 0x821E,
        "third_count": 0,
    }
    assert len(manifest["changed_bytes"]) == 20
    assert manifest["changed_bytes"][0] == {"absolute_offset": "0x003200", "before": 8, "after": 9}
    assert manifest["changed_bytes"][1]["absolute_offset"] == "0x0032ac"


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_language9_probe_roundtrips_to_exact_original():
    original, probe, _manifest = MODULE.prepare(IMAGE.read_bytes())
    restored = bytearray(probe)
    restored[:] = original
    assert bytes(restored) == original
    assert MODULE.sha256(restored) == "95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9"


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_language9_probe_refuses_wrong_image_hash():
    changed = bytearray(IMAGE.read_bytes())
    changed[0] ^= 1
    with pytest.raises(ValueError, match="unqualified image"):
        MODULE.prepare(bytes(changed))


def test_openocd_language_gates_are_exact_crc_locked():
    openocd_path = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
    spec = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd_language", openocd_path)
    openocd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(openocd)
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    install = openocd.derive(template, "language9-install")
    assert "language9_install.bin" in install
    assert "magic == 0x4b574e49" in install
    assert "$target_crc == 0xf5c23372" in install
    assert "$buffer_crc == 0xfa2d76bb" in install
    assert "$final_crc == 0xfa2d76bb" in install
    assert install.count("language9-test-sector-003000-chunk") == 4
    assert "STATUS_CLEAR_RETRY" in install
    restore = openocd.derive(template, "language9-restore")
    assert "language9_restore.bin" in restore
    assert "magic == 0x4b574e52" in restore
    assert "$target_crc == 0xfa2d76bb" in restore
    assert "$buffer_crc == 0xf5c23372" in restore
    assert "$final_crc == 0xf5c23372" in restore
    assert restore.count("original-sector-003000-chunk") == 4
