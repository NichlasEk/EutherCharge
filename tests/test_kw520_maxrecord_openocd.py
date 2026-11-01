import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_maxrecord_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_maxrecord_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_probe_and_restore_gates():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    probe = MODULE.derive(template, "probe")
    restore = MODULE.derive(template, "restore")
    assert "0x41524d45" in probe and "0x4b574d50" in probe
    assert "buffer_crc == 0xde37c157" in probe
    assert "target_crc == 0xf5c23372" in probe
    assert "final_crc == 0xde37c157" in probe
    assert probe.count("maxrecord-sector-003000-chunk") == 4
    assert "0x41524d46" in restore and "0x4b574d52" in restore
    assert "buffer_crc == 0xf5c23372" in restore
    assert "target_crc == 0xde37c157" in restore
    assert "final_crc == 0xf5c23372" in restore
    assert restore.count("original-sector-003000-chunk") == 4


def test_refuses_changed_template():
    template = bytearray((ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes())
    template[-1] ^= 1
    try:
        MODULE.derive(bytes(template), "probe")
    except ValueError as error:
        assert "refusing changed" in str(error)
    else:
        raise AssertionError("changed template accepted")
