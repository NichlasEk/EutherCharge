import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_four_address_and_crc_locked_gates():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    expected = {
        "data-install": ("0x41524d47", "0x4b574449", "0x6417ecbd", "0xf154670a", "0x6417ecbd", "data-test-sector-00c000-chunk"),
        "data-restore": ("0x41524d48", "0x4b574452", "0xf154670a", "0x6417ecbd", "0xf154670a", "data-original-sector-00c000-chunk"),
        "pointer-install": ("0x41524d49", "0x4b574f50", "0x6f68933f", "0xf5c23372", "0x6f68933f", "pointer-test-sector-003000-chunk"),
        "pointer-restore": ("0x41524d4a", "0x4b574f52", "0xf5c23372", "0x6f68933f", "0xf5c23372", "pointer-original-sector-003000-chunk"),
    }
    for mode, (arm, magic, buffer_crc, target_crc, final_crc, chunks) in expected.items():
        output = MODULE.derive(template, mode)
        assert arm in output and magic in output
        assert f"buffer_crc == {buffer_crc}" in output
        assert f"target_crc == {target_crc}" in output
        assert f"final_crc == {final_crc}" in output
        assert output.count(chunks) == 4


def test_refuses_changed_template():
    template = bytearray((ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes())
    template[-1] ^= 1
    try:
        MODULE.derive(bytes(template), "data-restore")
    except ValueError as error:
        assert "refusing changed" in str(error)
    else:
        raise AssertionError("changed template accepted")
