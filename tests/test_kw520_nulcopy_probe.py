import importlib.util
import struct
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_nulcopy_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_nulcopy_probe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
IMAGE = ROOT / "dumps" / "readback" / "kw520-after-euthercharge-2026-10-18.bin"


def test_payload_has_fixed_discriminator_and_preserved_return_word():
    payload = MODULE.build_payload()
    assert len(payload) == 320
    assert payload[100] == 0
    assert payload[101:117] == b"AFTER-NUL-MARKER"
    assert struct.unpack_from("<I", payload, 252)[0] == 0x080093F3
    assert payload[256:267] == b"TAIL-UNREAD"
    assert payload[-1] == 0
    assert b"%" not in payload


@pytest.mark.skipif(not IMAGE.exists(), reason="local qualified KW520 image is intentionally ignored")
def test_nulcopy_probe_is_sector_exact_and_reversible():
    sectors, manifest = MODULE.prepare(IMAGE.read_bytes())
    assert MODULE.crc32(sectors["pointer-original-sector-003000"]) == 0xF5C23372
    assert MODULE.crc32(sectors["pointer-test-sector-003000"]) == 0x6F68933F
    assert sectors["data-original-sector-00c000"] == b"\xff" * 0x1000
    assert len(sectors["nulcopy-data-test-sector-00c000"]) == 0x1000
    assert manifest["record"]["return_word_address"] == "0x20003a74"
    assert manifest["record"]["return_word_little_endian"] == "f3930008"
    assert manifest["safety"]["no_chosen_control_target"] is True


def test_nulcopy_openocd_data_gates_are_exact_crc_locked():
    path = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
    spec = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd_nulcopy", path)
    openocd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(openocd)
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    install = openocd.derive(template, "nulcopy-data-install")
    assert "nulcopy_data_install.bin" in install
    assert "magic == 0x4b574e44" in install
    assert "$target_crc == 0xf154670a" in install
    assert "$buffer_crc == 0x733066b3" in install
    assert "$final_crc == 0x733066b3" in install
    assert install.count("nulcopy-data-test-sector-00c000-chunk") == 4
    restore = openocd.derive(template, "nulcopy-data-restore")
    assert "nulcopy_data_restore.bin" in restore
    assert "magic == 0x4b575a52" in restore
    assert "$target_crc == 0x733066b3" in restore
    assert "$buffer_crc == 0xf154670a" in restore
    assert "$final_crc == 0xf154670a" in restore


def test_nulcopy_pointer_gates_have_dedicated_artifacts():
    path = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
    spec = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd_nulcopy_pointer", path)
    openocd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(openocd)
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    install = openocd.derive(template, "nulcopy-pointer-install")
    assert "boundary_pointer_install_retry.bin" in install
    assert "magic == 0x4b575849" in install
    assert "$target_crc == 0xf5c23372" in install
    assert "$final_crc == 0x6f68933f" in install
    assert install.count("build/kw520-nulcopy-probe/pointer-test-sector-003000-chunk") == 4
    restore = openocd.derive(template, "nulcopy-pointer-bitbang-restore")
    assert "frontier_pointer_bitbang_restore.bin" in restore
    assert "magic == 0x4b574652" in restore
    assert "$target_crc == 0x6f68933f" in restore
    assert "$final_crc == 0xf5c23372" in restore
    assert "BITBANG_REGS ok=%u" in restore
