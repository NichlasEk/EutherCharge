import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_boundary_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_boundary_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_three_crc_locked_gates():
    template = (ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes()
    baseline = MODULE.derive(template, "baseline")
    extend = MODULE.derive(template, "extend")
    restore = MODULE.derive(template, "restore")
    assert "0x41524d42" in baseline and "0x4b574253" in baseline
    assert "buffer_crc == 0xb461d992" in baseline and "target_crc == 0xf5c23372" in baseline
    assert "final_crc == 0xb461d992" in baseline
    assert "0x41524d43" in extend and "0x4b574558" in extend
    assert "buffer_crc == 0xe4e92a7b" in extend and "target_crc == 0xb461d992" in extend
    assert "final_crc == 0xe4e92a7b" in extend
    assert "0x41524d44" in restore and "0x4b574252" in restore
    assert "target_crc == 0xb461d992 || $target_crc == 0xe4e92a7b" in restore
    assert "final_crc == 0xf5c23372" in restore
    assert "0x6d0" in restore


def test_refuses_changed_template():
    template = bytearray((ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes())
    template[-1] ^= 1
    try:
        MODULE.derive(bytes(template), "baseline")
    except ValueError as error:
        assert "refusing changed" in str(error)
    else:
        raise AssertionError("changed template was accepted")
