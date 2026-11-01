import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_kw520_length_openocd.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_length_openocd", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_derives_length_probe_and_restore():
    probe_template = (ROOT / "tools/kw520_spi_patch/format-probe.cfg").read_bytes()
    restore_template = (ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes()
    probe = MODULE.derive_probe(probe_template)
    restore = MODULE.derive_restore(restore_template)
    assert "0x41524d39" in probe
    assert "0x4b574c4e" in probe
    assert "bytes_before == 0x0a00" in probe
    assert "bytes_after == 0x0800" in probe
    assert "crc_after == 0x5e1e3b15" in probe
    assert "length_probe.bin" in probe
    assert "0x690" in probe
    assert "0x41524d41" in restore
    assert "0x4b574c52" in restore
    assert "target_crc == 0x5e1e3b15" in restore
    assert "final_crc == 0xf5c23372" in restore
    assert "length_restore.bin" in restore
    assert "0x7985c2f6" not in probe
    assert "0x7985c2f6" not in restore


def test_refuses_changed_templates():
    probe = bytearray((ROOT / "tools/kw520_spi_patch/format-probe.cfg").read_bytes())
    restore = bytearray((ROOT / "tools/kw520_spi_patch/restore-noop.cfg").read_bytes())
    probe[-1] ^= 1
    restore[-1] ^= 1
    for function, data in ((MODULE.derive_probe, probe), (MODULE.derive_restore, restore)):
        try:
            function(bytes(data))
        except ValueError as error:
            assert "refusing changed" in str(error)
        else:
            raise AssertionError("changed OpenOCD template was accepted")
