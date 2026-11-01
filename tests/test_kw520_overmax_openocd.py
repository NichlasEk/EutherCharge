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


def test_derives_allocation_128_data_gates_and_reuses_pointer_helpers():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    expected = {
        "boundary128-data-install": ("boundary128_data_install", "0x41524d4b", "0x4b573849", "0x1f18aa83", "0xf154670a", "0x1f18aa83"),
        "boundary128-data-restore": ("boundary128_data_restore", "0x41524d4c", "0x4b573852", "0xf154670a", "0x1f18aa83", "0xf154670a"),
        "boundary128-pointer-install": ("overmax_pointer_install", "0x41524d49", "0x4b574f50", "0x6f68933f", "0xf5c23372", "0x6f68933f"),
        "boundary128-pointer-restore": ("overmax_pointer_restore", "0x41524d4a", "0x4b574f52", "0xf5c23372", "0x6f68933f", "0xf5c23372"),
    }
    for mode, (binary, arm, magic, buffer_crc, target_crc, final_crc) in expected.items():
        output = MODULE.derive(template, mode)
        assert f"build/kw520-spi-patch/{binary}.bin" in output
        assert arm in output and magic in output
        assert f"buffer_crc == {buffer_crc}" in output
        assert f"target_crc == {target_crc}" in output
        assert f"final_crc == {final_crc}" in output
        assert output.count("build/kw520-boundary128-probe/") == 4


def test_bounded_pointer_restore_requires_retry_telemetry():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary128-pointer-restore-retry")
    assert "build/kw520-spi-patch/boundary128_pointer_restore_retry.bin" in output
    assert "magic == 0x4b575852" in output
    assert "0x41524d4d" in output
    assert "STATUS_CLEAR_RETRY attempts=%u wren_last=%02x" in output
    assert "status_attempts >= 1 && $status_attempts <= 2" in output
    assert "status_wren_last == 0x1a" in output
    assert "status_attempts == 0 && $status_wren_last == 0" in output


def test_allocation_160_direct_transition_and_bounded_pointer_gates():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    data = MODULE.derive(template, "boundary160-data-install")
    assert "boundary160_data_install.bin" in data
    assert "target_crc == 0x1f18aa83" in data
    assert "buffer_crc == 0x0c91e3d5" in data
    assert "final_crc == 0x0c91e3d5" in data
    assert data.count("build/kw520-boundary160-probe/data-test-sector-00c000-chunk") == 4
    for mode, binary, magic in (
        ("boundary160-pointer-install-retry", "boundary_pointer_install_retry.bin", "0x4b575849"),
        ("boundary160-pointer-restore-retry", "boundary128_pointer_restore_retry.bin", "0x4b575852"),
    ):
        output = MODULE.derive(template, mode)
        assert binary in output and f"magic == {magic}" in output
        assert "status_attempts >= 1 && $status_attempts <= 2" in output
        assert output.count("build/kw520-boundary160-probe/") == 4


def test_allocation_192_direct_transition_gate():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    data = MODULE.derive(template, "boundary192-data-install")
    assert "boundary192_data_install.bin" in data
    assert "target_crc == 0x0c91e3d5" in data
    assert "buffer_crc == 0x80fff2a8" in data
    assert "status_attempts >= 1 && $status_attempts <= 2" in data
    for mode in ("boundary192-pointer-install-retry", "boundary192-pointer-restore-retry"):
        output = MODULE.derive(template, mode)
        assert output.count("build/kw520-boundary192-probe/") == 4
        assert "STATUS_CLEAR_RETRY" in output


def test_allocation_224_direct_transition_gate():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    data = MODULE.derive(template, "boundary224-data-install")
    assert "boundary224_data_install.bin" in data
    assert "target_crc == 0x80fff2a8" in data
    assert "buffer_crc == 0xff988d5c" in data
    for mode in ("boundary224-pointer-install-retry", "boundary224-pointer-restore-retry"):
        output = MODULE.derive(template, mode)
        assert output.count("build/kw520-boundary224-probe/") == 4
        assert "STATUS_CLEAR_RETRY" in output


def test_allocation_224_audit_stops_before_write_states():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary224-data-audit")
    assert "boundary_data_audit.bin" in output
    assert "state == 0x43" in output
    assert "magic == 0x4b574144" in output
    assert "set restore_ok 0" in output
    assert "target_crc ==" not in output
    assert "read-only allocation-224 data-sector audit completed" in output
    assert "state == 0x42 || $state == 0x43 || $state >= 0xe0" in output


def test_allocation_224_erased_recovery_accepts_only_all_ff():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary224-data-install-erased")
    assert "boundary224_data_install_erased.bin" in output
    assert "target_crc == 0xf154670a" in output
    assert "buffer_crc == 0xff988d5c" in output
    assert "final_crc == 0xff988d5c" in output
    assert "status_attempts >= 1 && $status_attempts <= 2" in output


def test_allocation_240_direct_transition_gate():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    data = MODULE.derive(template, "boundary240-data-install")
    assert "boundary240_data_install.bin" in data
    assert "target_crc == 0xff988d5c" in data
    assert "buffer_crc == 0xaba2265e" in data
    for mode in ("boundary240-pointer-install-retry", "boundary240-pointer-restore-retry"):
        output = MODULE.derive(template, mode)
        assert output.count("build/kw520-boundary240-probe/") == 4
        assert "STATUS_CLEAR_RETRY" in output


def test_allocation_240_final_restore_accepts_only_exact_test_crc():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-data-restore")
    assert "boundary240_data_restore.bin" in output
    assert "target_crc == 0xaba2265e" in output
    assert "buffer_crc == 0xf154670a" in output
    assert "final_crc == 0xf154670a" in output
    assert output.count("data-original-sector-00c000-chunk") == 4


def test_partial_pointer_audit_is_read_only_and_unconditional_on_target_crc():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-pointer-audit")
    assert "boundary_pointer_audit.bin" in output
    assert "state == 0x43" in output
    assert "magic == 0x4b575041" in output
    assert "target_crc ==" not in output
    assert output.count("pointer-original-sector-003000-chunk") == 4
    assert "set rec_acfgr" in output and "set rec_apb1en" in output
    assert "write_memory 0x48000018 32 {0x00000100}" in output
    assert "($rec_bpull & ~(0x3f << 26)) | (0x04 << 26)" in output
    assert "write_memory 0x40003800 32 {0x00000357}" in output
    assert "write_memory 0x40021014 32 [list $rec_ahben]" in output


def test_partial_pointer_bitbang_audit_uses_only_fixed_gpio_roles():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-pointer-bitbang-audit")
    assert "boundary_pointer_bitbang_audit.bin" in output
    assert "magic == 0x4b574241" in output and "state == 0x43" in output
    assert "write_memory 0x48000018 32 {0x00000100}" in output
    assert "write_memory 0x48000428 32 {0x00002000}" in output
    assert "write_memory 0x48000418 32 {0x00008000}" in output
    assert "($rec_bcfgr & ~(0x3f << 26)) | (0x11 << 26)" in output
    assert "write_memory 0x48000414 32 [list $rec_bodt]" in output
    assert "BITBANG_REGS ok=%u" in output
    assert "live PA8/SPI2 configuration" not in output


def test_partial_pointer_bitbang_restore_is_exact_crc_gated():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-pointer-bitbang-restore")
    assert "boundary_pointer_bitbang_restore.bin" in output
    assert "magic == 0x4b574252" in output
    assert "$target_crc == 0x33e293e2" in output
    assert "$final_crc == 0xf5c23372" in output
    assert "BITBANG_REGS ok=%u" in output
    assert "STATUS_CLEAR_RETRY attempts=%u" in output


def test_interrupted_pointer_audit_accepts_only_status_02():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-pointer-interrupted-audit")
    assert "boundary_pointer_interrupted_audit.bin" in output
    assert "magic == 0x4b574249" in output
    assert "$status == 0x02" in output
    assert "state == 0x43" in output


def test_interrupted_pointer_restore_has_exact_gate_and_long_wait():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-pointer-interrupted-restore")
    assert "boundary_pointer_interrupted_restore.bin" in output
    assert "magic == 0x4b574952" in output
    assert "$status == 0x02" in output
    assert "$target_crc == 0x559db759" in output
    assert "$final_crc == 0xf5c23372" in output
    assert "{$i < 4000}" in output


def test_boundary240_data_restore_keeps_long_host_wait():
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    output = MODULE.derive(template, "boundary240-data-restore")
    assert "{$i < 4000}" in output
    assert "$target_crc == 0xaba2265e" in output
    assert "$final_crc == 0xf154670a" in output
