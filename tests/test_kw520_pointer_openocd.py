import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_pointer_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_pointer_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_only_fixed_pointer_probe_gate():
    template = (ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "probe")

    assert "0x41524d35" in output
    assert "0x4b575044" in output
    assert "pointer_probe.bin" in output
    assert output.count("pointer-sector-003000-chunk") == 4
    assert "buffer_crc == 0x14b0524b" in output
    assert "target_crc == 0xf5c23372" in output
    assert "final_crc == 0x14b0524b" in output
    assert "exact same-bank pointer probe programmed and verified" in output
    assert "0x7985c2f6" not in output
    assert "0x41524d32" not in output


def test_refuses_changed_template():
    template = bytearray((ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes())
    template[-1] ^= 1
    try:
        MODULE.derive(bytes(template), "probe")
    except ValueError as error:
        assert "refusing changed restore template" in str(error)
    else:
        raise AssertionError("changed OpenOCD template was accepted")


def test_derives_fixed_pointer_restore_gate():
    template = (ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "restore")

    assert "0x41524d36" in output
    assert "0x4b57524f" in output
    assert "pointer_restore.bin" in output
    assert output.count("restore-sector-003000-chunk") == 4
    assert "buffer_crc == 0xf5c23372" in output
    assert "target_crc == 0x14b0524b" in output
    assert "final_crc == 0xf5c23372" in output
    assert "exact pointer-probe sector restored and verified" in output
    assert "0x7985c2f6" not in output
