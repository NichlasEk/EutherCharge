import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "tools" / "kw520_call_oracle" / "oracle.S"
LINKER = ROOT / "tools" / "kw520_call_oracle" / "linker.ld"
README = ROOT / "tools" / "kw520_call_oracle" / "README.md"
INVENTORY = ROOT / "tools" / "kw520_call_oracle" / "inventory.cfg"
RUNNER = ROOT / "tools" / "kw520_call_oracle" / "run-inventory.sh"
CANDIDATE_CFG = ROOT / "tools" / "kw520_call_oracle" / "candidate18.cfg"
CANDIDATE_RUNNER = ROOT / "tools" / "kw520_call_oracle" / "run-candidate18.sh"
DETACH_ARM = ROOT / "tools" / "kw520_call_oracle" / "detach-arm.cfg"
DETACH_READBACK = ROOT / "tools" / "kw520_call_oracle" / "detach-readback.cfg"
DETACH_RUNNER = ROOT / "tools" / "kw520_call_oracle" / "run-detach18.sh"


def test_oracle_has_inventory_arm_and_mpu_gates():
    text = SOURCE.read_text(encoding="utf-8")
    assert ".equ ARM_MAGIC,       0x43414c4c" in text
    assert "ubfx r1, r1, #8, #8" in text
    assert "cmp r1, #6" in text
    assert "cmp r1, #CANDIDATE_COUNT" in text
    assert "movs r1, #1            /* ENABLE, no PRIVDEFENA, no HFNMIENA */" in text
    assert ".equ MPU_FLASH_64K_RO_X,  0x0602001f" in text
    assert ".equ MPU_DATA_256_RO_XN, 0x1602000f" in text
    configure = text.split("configure_mpu:\n", 1)[1].split(".size configure_mpu", 1)[0]
    assert "push {lr}" in configure
    assert "pop {pc}" in configure


def test_candidate_is_unprivileged_and_peripheral_space_is_not_mapped():
    text = SOURCE.read_text(encoding="utf-8")
    assert "msr psp, r1" in text
    assert "msr control, r1" in text
    assert "blx r4" in text
    assert "udf #0" in text
    assert "0x40000000" not in text
    assert "0x48000000" not in text
    assert "PRIVDEFENA" in text
    assert "No GPIO, SPI, flash controller" in README.read_text(encoding="utf-8")


def test_detach_command_waits_for_debug_disable_before_mpu_call():
    text = SOURCE.read_text(encoding="utf-8")
    assert "cmp r1, #3" in text
    assert ".equ DHCSR,           0xe000edf0" in text
    detached = text.split("wait_for_debug_detach:\n", 1)[1].split("configure_for_call:\n", 1)[0]
    assert "movs r1, #0x40" in detached
    assert "ldr r1, =DHCSR" in detached
    assert "tst r2, #1" in detached
    assert "bne detach_poll" in detached
    assert "movs r1, #0x41" in detached
    assert "ldr r3, =2000000" in detached
    assert "bne detach_guard_delay" in detached


def test_candidate_table_is_fixed_thumb_main_flash_values():
    text = SOURCE.read_text(encoding="utf-8")
    table = text.split("candidate_table:\n", 1)[1]
    values = [int(value, 16) for value in re.findall(r"\.word (0x[0-9a-f]+)", table)]
    assert len(values) == 19
    assert len(values) == len(set(values))
    assert all(0x08000001 <= value <= 0x0800FFFF and value & 1 for value in values)


def test_linker_hard_limits_executable_oracle_to_one_kibibyte():
    text = LINKER.read_text(encoding="utf-8")
    assert "ORIGIN = 0x20001000, LENGTH = 0x400" in text
    assert "call oracle exceeds MPU-protected code region" in text


def test_inventory_runner_cannot_arm_or_invoke_candidate():
    cfg = INVENTORY.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    assert "write_memory 0x2000170c 32 {1}" in cfg
    assert "0x20001708" not in cfg
    assert "write_memory 0x20001710" not in cfg
    assert "command 1" in cfg
    assert "never arms" in cfg
    assert "cmp -s build/kw520-call-oracle/oracle.bin" in runner
    assert 'cmp -s "$out/sram-backup.bin" "$out/sram-restored.bin"' in runner
    assert 'dump_image "$out/sram-backup.bin" 0x20001000 0x1300' in cfg
    assert 'dump_image "$out/sram-restored.bin" 0x20001000 0x1300' in cfg
    assert "openocd_status=${PIPESTATUS[0]}" in runner
    for forbidden in ("flash write", "unlock", "recover", "mass erase"):
        assert forbidden not in cfg.lower()


def test_candidate_runner_is_fixed_to_index_18_and_sram_only():
    cfg = CANDIDATE_CFG.read_text(encoding="utf-8")
    runner = CANDIDATE_RUNNER.read_text(encoding="utf-8")
    assert "write_memory 0x20001710 32 {18}" in cfg
    assert "candidate == 0x0800ad8f" in cfg
    assert "write_memory 0x20001708 32 {0x43414c4c}" in cfg
    assert "write_memory 0x2000170c 32 {2}" in cfg
    assert "dump_image \"$out/oracle-data.bin\" 0x20001800 0x200" in cfg
    assert "write_memory 0xe000ed94 32 {0}" in cfg
    assert 'dump_image "$out/sram-restored.bin" 0x20001000 0x1300' in cfg
    assert "--candidate-18-sram-copy" in runner
    assert "candidate 18 was contained" in runner
    for forbidden in ("0x08000000", "flash write", "unlock", "recover", "mass erase"):
        assert forbidden not in cfg.lower()


def test_detach_gate_is_two_phase_fixed_candidate_and_restores_second():
    arm = DETACH_ARM.read_text(encoding="utf-8")
    readback = DETACH_READBACK.read_text(encoding="utf-8")
    runner = DETACH_RUNNER.read_text(encoding="utf-8")
    assert "write_memory 0x20001710 32 {18}" in arm
    assert "write_memory 0x2000170c 32 {3}" in arm
    assert "state == 0x40" in arm
    assert "ACCEPTED: candidate 18 is waiting for debug detach" in arm
    assert "write_memory 0xe000edf0 32 {0xa05f0000}" in arm
    assert "kw520.dap dpreg 4 0x40000000" in arm
    assert "DETACH_RELEASE status=$release_status" in arm
    assert "load_image \"$out/sram-backup.bin\"" not in arm.split('puts "ACCEPTED:', 1)[1]
    assert "DETACH_OUTCOME exact-copy" in readback
    assert "DETACH_OUTCOME debug-never-detached" in readback
    assert "write_memory 0xe000ed94 32 {0}" in readback
    assert "write_memory 0xe000ed08 32 {0x08000000}" in readback
    assert 'load_image "$out/sram-backup.bin" 0x20001000 bin' in readback
    assert "--detach-candidate-18-sram-copy" in runner
    assert "sleep 1" in runner
    assert "arm_gate=0" in runner and "[[ $arm_gate == 1 ]]" in runner
    assert "DETACH_RELEASE status=0xc0000040" in runner
    assert runner.index('[[ -f $out/sram-backup.bin ]]') < runner.index("detach-readback.cfg")
    assert runner.index("detach-arm.cfg") < runner.index("detach-readback.cfg")
    for text in (arm, readback):
        for forbidden in ("flash write", "unlock", "recover", "mass erase"):
            assert forbidden not in text.lower()
