import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_language_list_gate.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_language_list_gate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
IMAGE = ROOT / "dumps" / "readback" / "kw520-after-euthercharge-2026-10-18.bin"


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_consistent_language9_list_probe():
    original, probe, manifest = MODULE.prepare(IMAGE.read_bytes())
    assert len(original) == len(probe) == 0x1000
    assert MODULE.BASE.crc32(original) == 0xF5C23372
    assert MODULE.BASE.crc32(probe) == 0x4779B7F4
    assert MODULE.BASE.sha256(probe) == MODULE.EXPECTED_PROBE_SHA256
    assert manifest["language_list"]["ids_after"] == [3, 4, 5, 6, 7, 8, 9, 10, 14]
    assert manifest["directory"]["active_ids_after"] == [3, 4, 5, 6, 7, 8, 9, 10, 14]
    assert len(manifest["changed_bytes"]) == 24
    offsets = [item["absolute_offset"] for item in manifest["changed_bytes"]]
    assert offsets[:4] == ["0x003041", "0x003049", "0x00304a", "0x00304b"]
    assert offsets[4] == "0x003200"
    assert offsets[5] == "0x0032ac"


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_consistent_language9_probe_preserves_selected_language():
    original, probe, _manifest = MODULE.prepare(IMAGE.read_bytes())
    selected = MODULE.SELECTED_ID_OFFSET - MODULE.BASE.SECTOR_START
    assert original[selected] == probe[selected] == 3


def test_list_openocd_gates_are_exact_crc_locked():
    openocd_path = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
    spec = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd_list", openocd_path)
    openocd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(openocd)
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    install = openocd.derive(template, "language9-list-install")
    assert "language9_list_install.bin" in install
    assert "magic == 0x4b574c49" in install
    assert "$target_crc == 0xf5c23372" in install
    assert "$buffer_crc == 0x4779b7f4" in install
    assert "$final_crc == 0x4779b7f4" in install
    assert install.count("language9-listed-test-sector-003000-chunk") == 4
    restore = openocd.derive(template, "language9-list-restore")
    assert "language9_list_restore.bin" in restore
    assert "magic == 0x4b574c52" in restore
    assert "$target_crc == 0x4779b7f4" in restore
    assert "$buffer_crc == 0xf5c23372" in restore
    assert "$final_crc == 0xf5c23372" in restore
