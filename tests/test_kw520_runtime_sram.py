from pathlib import Path


ROOT = Path(__file__).parents[1]
CFG = ROOT / "tools" / "kw520_runtime_sram" / "capture.cfg"
RUNNER = ROOT / "tools" / "kw520_runtime_sram" / "run-capture.sh"


def test_capture_is_fixed_read_only_full_sram_gate():
    text = CFG.read_text(encoding="utf-8")
    commands = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    assert "KW520_RUNTIME_SRAM_OUTPUT is required" in text
    assert "dump_image $::env(KW520_RUNTIME_SRAM_OUTPUT) 0x20000000 0x4000" in text
    assert "RUNTIME_SRAM_CAPTURE=PASS" in text
    for forbidden in ("mww ", "mwh ", "mwb ", "load_image", "resume", "reset run", "flash write"):
        assert forbidden not in commands


def test_runner_requires_label_and_exact_size():
    text = RUNNER.read_text(encoding="utf-8")
    assert '"--capture"' in text
    assert "Refusing to replace existing capture or log" in text
    assert "size != 16384" in text
    assert 'grep -Fq "RUNTIME_SRAM_CAPTURE=PASS"' in text
