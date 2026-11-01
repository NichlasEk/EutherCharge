import importlib.util
import struct
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
PREPARE_PATH = ROOT / "tools" / "prepare_kw520_stack_exec_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_stack_exec_probe_test", PREPARE_PATH)
PREPARE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARE)
ANALYZE_PATH = ROOT / "tools" / "kw520_stack_exec_probe" / "analyze_capture.py"
ASPEC = importlib.util.spec_from_file_location("analyze_kw520_stack_exec_probe_test", ANALYZE_PATH)
ANALYZE = importlib.util.module_from_spec(ASPEC)
assert ASPEC.loader is not None
ASPEC.loader.exec_module(ANALYZE)
IMAGE = ROOT / "dumps" / "readback" / "kw520-after-euthercharge-2026-10-18.bin"
STUB = ROOT / "build" / "kw520-stack-exec-probe" / "stub.bin"


@pytest.mark.skipif(not STUB.exists(), reason="build the fixed marker stub first")
def test_stub_and_payload_are_fixed():
    stub = STUB.read_bytes()
    payload = PREPARE.build_payload(stub)
    assert len(stub) == 32
    assert len(payload) == 320
    assert struct.unpack_from("<I", payload, 252)[0] == 0x20003979
    assert payload[:32] == stub
    assert payload[-1] == 0


@pytest.mark.skipif(not IMAGE.exists() or not STUB.exists(), reason="local qualified inputs are ignored")
def test_exec_probe_is_sector_exact():
    sectors, manifest = PREPARE.prepare(IMAGE.read_bytes(), STUB.read_bytes())
    assert PREPARE.crc32(sectors["pointer-original-sector-003000"]) == 0xF5C23372
    assert PREPARE.crc32(sectors["pointer-test-sector-003000"]) == 0x6F68933F
    assert sectors["data-original-sector-00c000"] == b"\xff" * 0x1000
    assert len(sectors["exec-data-test-sector-00c000"]) == 0x1000
    assert manifest["stub"]["entry"] == "0x20003979"
    assert manifest["safety"]["stub_accesses_peripherals"] is False


@pytest.mark.skipif(not STUB.exists(), reason="build the fixed marker stub first")
def test_capture_analyzer_requires_payload_and_mailbox():
    stub = STUB.read_bytes()
    payload = PREPARE.build_payload(stub)
    sram = bytearray(0x4000)
    buffer = PREPARE.BUFFER_ADDRESS - 0x20000000
    mailbox = PREPARE.MAILBOX_ADDRESS - 0x20000000
    sram[buffer:buffer + 256] = payload[:256]
    assert ANALYZE.analyze(bytes(sram), stub)["control_flow_qualified"] is False
    sram[mailbox:mailbox + len(PREPARE.MAILBOX)] = PREPARE.MAILBOX
    assert ANALYZE.analyze(bytes(sram), stub)["control_flow_qualified"] is True


def test_stack_exec_openocd_gates_are_exact_crc_locked():
    path = ROOT / "tools" / "prepare_kw520_overmax_openocd.py"
    spec = importlib.util.spec_from_file_location("prepare_kw520_overmax_openocd_exec", path)
    openocd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(openocd)
    template = (ROOT / "tools" / "kw520_spi_patch" / "restore-noop.cfg").read_bytes()
    expected = {
        "stack-exec-data-install": ("0x4b574549", "0xf154670a", "0x041ae9b0"),
        "stack-exec-data-restore": ("0x4b574552", "0x041ae9b0", "0xf154670a"),
        "stack-exec-pointer-install": ("0x4b575849", "0xf5c23372", "0x6f68933f"),
        "stack-exec-pointer-bitbang-restore": ("0x4b574652", "0x6f68933f", "0xf5c23372"),
    }
    for mode, (magic, target, final) in expected.items():
        output = openocd.derive(template, mode)
        assert f"magic == {magic}" in output
        assert f"$target_crc == {target}" in output
        assert f"$final_crc == {final}" in output
        assert output.count("build/kw520-stack-exec-probe/") >= 4
    restore = openocd.derive(template, "stack-exec-pointer-bitbang-restore")
    assert "BITBANG_REGS ok=%u" in restore
