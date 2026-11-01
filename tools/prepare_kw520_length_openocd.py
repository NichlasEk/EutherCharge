#!/usr/bin/env python3
"""Derive fixed length-shortening probe/restore gates from qualified templates."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PROBE_TEMPLATE_SHA256 = "95275204fd8466ca9902d0861178662908fc5ea6c0809e2668e5ae8bdbc9b44e"
RESTORE_TEMPLATE_SHA256 = "710926ea8b61331246bb235f1466bf8efc42e2191b2da90774f4b3db211b4704"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_exact(text: str, old: str, new: str, count: int) -> str:
    actual = text.count(old)
    if actual != count:
        raise ValueError(f"template token count {actual}, expected {count}: {old!r}")
    return text.replace(old, new)


def derive_probe(template: bytes) -> str:
    digest = sha256(template)
    if digest != PROBE_TEMPLATE_SHA256:
        raise ValueError(f"refusing changed probe template {digest}")
    text = template.decode("utf-8")
    text = replace_exact(
        text,
        "# Fixed two-byte parser probe at 0x003899. This can only change 6d65 -> 2525,\n"
        "# verifies the complete sector CRC, and has no erase or generic address path.",
        "# Fixed main-title length shortening at 0x003892: 000a -> 0008.\n"
        "# Copy length only decreases; full sector CRC is verified and there is no erase.",
        1,
    )
    text = replace_exact(text, "format-probe-", "length-probe-", 11)
    text = replace_exact(text, "format_probe.bin", "length_probe.bin", 1)
    text = replace_exact(text, "0x41524d31", "0x41524d39", 2)
    text = replace_exact(text, "FORMAT_PROBE", "LENGTH_PROBE", 1)
    text = replace_exact(
        text,
        "set accepted [expr {$core_ok && $done && $magic == 0x4b575050 && $state == 0x41 && $arm == 0x41524d39 && $jedec == 0x1c3016 && $status_before == 0x18 && $protection == 0xff && $bytes_before == 0x656d && $status_wren_clear == 0x1a && $status_cleared == 0 && $status_wren == 0x02 && $status_program == 0 && $bytes_after == 0x2525 && $crc_before == 0xf5c23372 && $crc_after == 0x7985c2f6 && $status_wren_restore == 0x02 && $status_restored == 0x18 && $spi_error == 0 && $cleanup == 0}]",
        "set accepted [expr {$core_ok && $done && $magic == 0x4b574c4e && $state == 0x41 && $arm == 0x41524d39 && $jedec == 0x1c3016 && $status_before == 0x18 && $protection == 0xff && $bytes_before == 0x0a00 && $status_wren_clear == 0x1a && $status_cleared == 0 && $status_wren == 0x02 && $status_program == 0 && $bytes_after == 0x0800 && $crc_before == 0xf5c23372 && $crc_after == 0x5e1e3b15 && $status_wren_restore == 0x02 && $status_restored == 0x18 && $spi_error == 0 && $cleanup == 0}]",
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: exact two-byte format probe programmed and sector verified"',
        'puts "ACCEPTED: exact declared-length shortening programmed and verified"',
        1,
    )
    text = replace_exact(
        text,
        'puts "REFUSED: fixed format-probe gate did not pass"',
        'puts "REFUSED: fixed declared-length probe gate did not pass"',
        1,
    )
    text = replace_exact(text, "0x698", "0x690", 1)
    return text


def derive_restore(template: bytes) -> str:
    digest = sha256(template)
    if digest != RESTORE_TEMPLATE_SHA256:
        raise ValueError(f"refusing changed restore template {digest}")
    text = template.decode("utf-8")
    text = replace_exact(
        text,
        "# Qualify the fixed sector-restoration helper against an already-correct sector.\n"
        "# Accepted result is state 0x42: no Write Enable, erase, or program executed.",
        "# Restore only the exact declared-length shortening to the original sector.\n"
        "# Accept only length CRC 5e1e3b15 or an already-restored no-op state.",
        1,
    )
    text = replace_exact(text, "restore-noop-", "length-restore-", 27)
    text = replace_exact(
        text,
        "build/kw520-format-probe/restore-sector-003000-chunk",
        "build/kw520-length-probe/restore-sector-003000-chunk",
        4,
    )
    text = replace_exact(
        text,
        "build/kw520-spi-patch/restore_sector.bin",
        "build/kw520-spi-patch/length_restore.bin",
        1,
    )
    text = replace_exact(text, "0x41524d32", "0x41524d41", 1)
    text = replace_exact(text, "RESTORE_NOOP", "LENGTH_RESTORE", 1)
    text = replace_exact(text, "0x4b575052", "0x4b574c52", 2)
    text = replace_exact(
        text,
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b574c52 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x7985c2f6 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b574c52 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x5e1e3b15 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: fixed restore helper exited before Write Enable"',
        'puts "ACCEPTED: original sector already present; no length restore write"',
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: exact format-probe sector restored and verified"',
        'puts "ACCEPTED: exact declared-length sector restored and verified"',
        1,
    )
    text = replace_exact(
        text,
        'puts "REFUSED: fixed restore no-op gate did not pass"',
        'puts "REFUSED: fixed declared-length restore gate did not pass"',
        1,
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("probe", "restore"), required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    derive = derive_probe if args.mode == "probe" else derive_restore
    output = derive(args.template.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} ({sha256(output.encode('utf-8'))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
