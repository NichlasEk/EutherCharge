import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "kw520_stack_frontier" / "analyze_capture.py"
SPEC = importlib.util.spec_from_file_location("kw520_stack_frontier_analyze", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def core_line(**overrides):
    fields = {
        "dhcsr": 0x00030003, "icsr": 3, "vtor": 0x08000000, "shcsr": 0,
        "cfsr": 0x00020000, "hfsr": 0x40000000, "mmfar": 0, "bfar": 0,
        "msp": 0x20003B00, "psp": 0x20003B00, "special": 0,
        "xpsr": 0x01000003, "pc": 0x08001235, "lr": 0xFFFFFFF9,
    }
    fields.update(overrides)
    return "FRONTIER_CORE " + " ".join(f"{name}={value:08x}" for name, value in fields.items()) + "\nFRONTIER_CAPTURE=PASS\n"


def test_exact_payload_and_stacked_pattern_pc_are_reported():
    allocation = 512
    visible, payload, _record, _sector = MODULE.frontier.record_for(allocation)
    sram = bytearray(b"\0" * MODULE.SRAM_SIZE)
    start = MODULE.BUFFER_ADDRESS - MODULE.SRAM_BASE
    sram[start : start + len(payload)] = payload
    stacked_pc_offset = 333
    stacked_pc = struct.unpack_from("<I", visible, stacked_pc_offset)[0]
    frame = (0, 0, 0, 0, 0, 0x08000001, stacked_pc, 0x01000000)
    struct.pack_into("<8I", sram, 0x3800, *frame)
    result = MODULE.analyze(bytes(sram), core_line(msp=0x20003800), allocation)
    assert result["payload_exact_at_buffer"] is True
    assert result["marker_occurrences"] == ["0x20003978"]
    assert result["exception_frame"]["pattern_offsets"]["pc"]["offset"] == stacked_pc_offset
    assert result["control_candidate"] is True


def test_320_capture_stops_at_256_byte_prefix_without_false_control_candidate():
    allocation = 320
    _visible, payload, _record, _sector = MODULE.frontier.record_for(allocation)
    sram = bytearray(b"\0" * MODULE.SRAM_SIZE)
    start = MODULE.BUFFER_ADDRESS - MODULE.SRAM_BASE
    sram[start : start + 256] = payload[:256]
    sram[start + 256] = 0
    preserved = bytes.fromhex("020000004010000800000000")
    sram[start + 260 : start + 260 + len(preserved)] = preserved
    frame = (0x48000400, 0x100, 0x6BCD, 0, 0x20003B44, 0x0800802F, 0x08010000, 0x01000000)
    struct.pack_into("<8I", sram, 0x3B88, *frame)

    result = MODULE.analyze(
        bytes(sram),
        core_line(
            msp=0x20003B88,
            psp=0,
            pc=0,
            cfsr=0x00020100,
            mmfar=0x20003B9C,
            bfar=0x20003B9C,
            xpsr=3,
        ),
        allocation,
    )

    assert result["payload_prefix_bytes"] == 256
    assert result["payload_exact_at_buffer"] is False
    assert result["register_pattern_offsets"] == {}
    assert result["exception_frame"]["pattern_offsets"] == {}
    assert result["control_candidate"] is False


def test_capture_config_has_no_sram_load_reset_or_resume():
    text = (ROOT / "tools" / "kw520_stack_frontier" / "capture.cfg").read_text()
    assert "dump_image $::env(KW520_FRONTIER_SRAM_OUTPUT) 0x20000000 0x4000" in text
    assert "FRONTIER_CORE" in text and "FRONTIER_CAPTURE=PASS" in text
    assert "load_image" not in text
    assert "resume" not in text
    assert "reset" not in text.replace("reset_config none", "")


def test_baseline_analysis_keeps_core_and_hash_only():
    sram = bytearray(MODULE.SRAM_SIZE)
    struct.pack_into("<8I", sram, 0x3B00, 1, 2, 3, 4, 5, 0x08001235, 0x08005679, 0x21000000)
    result = MODULE.analyze_baseline(bytes(sram), core_line(xpsr=0x01000000))
    assert result["baseline"] is True
    assert result["active_exception"] == 0
    assert result["core"]["msp"] == "0x20003b00"
    assert result["exception_frame"]["words"]["pc"] == "0x08005679"
