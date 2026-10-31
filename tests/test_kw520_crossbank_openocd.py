import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_crossbank_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_crossbank_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_crossbank_probe_and_restore_gates():
    template = (ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes()
    probe = MODULE.derive(template, "probe")
    restore = MODULE.derive(template, "restore")

    assert "0x41524d37" in probe
    assert "0x4b574342" in probe
    assert "crossbank_probe.bin" in probe
    assert probe.count("crossbank-sector-003000-chunk") == 4
    assert "buffer_crc == 0xb29ee7d1" in probe
    assert "target_crc == 0xf5c23372" in probe
    assert "final_crc == 0xb29ee7d1" in probe
    assert "cross-bank pointer probe programmed and verified" in probe

    assert "0x41524d38" in restore
    assert "0x4b574352" in restore
    assert "crossbank_restore.bin" in restore
    assert restore.count("restore-sector-003000-chunk") == 4
    assert "buffer_crc == 0xf5c23372" in restore
    assert "target_crc == 0xb29ee7d1" in restore
    assert "final_crc == 0xf5c23372" in restore
    assert "cross-bank pointer sector restored and verified" in restore
    assert "0x7985c2f6" not in probe
    assert "0x7985c2f6" not in restore


def test_refuses_changed_template():
    template = bytearray((ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes())
    template[-1] ^= 1
    try:
        MODULE.derive(bytes(template), "probe")
    except ValueError as error:
        assert "refusing changed restore template" in str(error)
    else:
        raise AssertionError("changed OpenOCD template was accepted")
