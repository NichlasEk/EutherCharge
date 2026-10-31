#!/usr/bin/env python3
"""Derive fixed cross-bank probe/restore gates from the qualified restore gate."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


TEMPLATE_SHA256 = "710926ea8b61331246bb235f1466bf8efc42e2191b2da90774f4b3db211b4704"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_exact(text: str, old: str, new: str, count: int) -> str:
    actual = text.count(old)
    if actual != count:
        raise ValueError(f"template token count {actual}, expected {count}: {old!r}")
    return text.replace(old, new)


def checked_template(template: bytes) -> str:
    digest = sha256(template)
    if digest != TEMPLATE_SHA256:
        raise ValueError(
            f"refusing changed restore template {digest}; expected {TEMPLATE_SHA256}"
        )
    return template.decode("utf-8")


def derive_probe(template: bytes) -> str:
    text = checked_template(template)
    text = replace_exact(
        text,
        "# Qualify the fixed sector-restoration helper against an already-correct sector.\n"
        "# Accepted result is state 0x42: no Write Enable, erase, or program executed.",
        "# Fixed valid cross-bank pointer: Huvudmeny entry -> French Menu principal.\n"
        "# Accept only exact original-to-cross-bank replacement or its no-op rerun.",
        1,
    )
    text = replace_exact(text, "restore-noop-", "crossbank-probe-", 27)
    text = replace_exact(
        text,
        "build/kw520-format-probe/restore-sector-003000-chunk",
        "build/kw520-crossbank-probe/crossbank-sector-003000-chunk",
        4,
    )
    text = replace_exact(
        text,
        "build/kw520-spi-patch/restore_sector.bin",
        "build/kw520-spi-patch/crossbank_probe.bin",
        1,
    )
    text = replace_exact(text, "0x41524d32", "0x41524d37", 1)
    text = replace_exact(text, "RESTORE_NOOP", "CROSSBANK_PROBE", 1)
    text = replace_exact(
        text,
        "set noop_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x42 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0xf5c23372 && $erased_crc == 0 && $final_crc == 0 && $pages == 0 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0 && $cleanup == 0}]",
        "set noop_ok [expr {$core_ok && $done && $magic == 0x4b574342 && $state == 0x42 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xb29ee7d1 && $target_crc == 0xb29ee7d1 && $erased_crc == 0 && $final_crc == 0 && $pages == 0 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0 && $cleanup == 0}]",
        1,
    )
    text = replace_exact(
        text,
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x7985c2f6 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b574342 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xb29ee7d1 && $target_crc == 0xf5c23372 && $erased_crc == 0xf154670a && $final_crc == 0xb29ee7d1 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: fixed restore helper exited before Write Enable"',
        'puts "ACCEPTED: exact cross-bank sector already present; no write"',
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: exact format-probe sector restored and verified"',
        'puts "ACCEPTED: exact cross-bank pointer probe programmed and verified"',
        1,
    )
    text = replace_exact(
        text,
        'puts "REFUSED: fixed restore no-op gate did not pass"',
        'puts "REFUSED: fixed cross-bank pointer-probe gate did not pass"',
        1,
    )
    return text


def derive_restore(template: bytes) -> str:
    text = checked_template(template)
    text = replace_exact(
        text,
        "# Qualify the fixed sector-restoration helper against an already-correct sector.\n"
        "# Accepted result is state 0x42: no Write Enable, erase, or program executed.",
        "# Restore only the exact valid cross-bank pointer probe to the original sector.\n"
        "# Accept only cross-bank CRC b29ee7d1 or an already-restored no-op state.",
        1,
    )
    text = replace_exact(text, "restore-noop-", "crossbank-restore-", 27)
    text = replace_exact(
        text,
        "build/kw520-format-probe/restore-sector-003000-chunk",
        "build/kw520-crossbank-probe/restore-sector-003000-chunk",
        4,
    )
    text = replace_exact(
        text,
        "build/kw520-spi-patch/restore_sector.bin",
        "build/kw520-spi-patch/crossbank_restore.bin",
        1,
    )
    text = replace_exact(text, "0x41524d32", "0x41524d38", 1)
    text = replace_exact(text, "RESTORE_NOOP", "CROSSBANK_RESTORE", 1)
    text = replace_exact(text, "0x4b575052", "0x4b574352", 2)
    text = replace_exact(
        text,
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b574352 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x7985c2f6 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        "set restore_ok [expr {$core_ok && $done && $magic == 0x4b574352 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0xb29ee7d1 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]",
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: fixed restore helper exited before Write Enable"',
        'puts "ACCEPTED: original sector already present; no cross-bank restore write"',
        1,
    )
    text = replace_exact(
        text,
        'puts "ACCEPTED: exact format-probe sector restored and verified"',
        'puts "ACCEPTED: exact cross-bank pointer sector restored and verified"',
        1,
    )
    text = replace_exact(
        text,
        'puts "REFUSED: fixed restore no-op gate did not pass"',
        'puts "REFUSED: fixed cross-bank restore gate did not pass"',
        1,
    )
    return text


def derive(template: bytes, mode: str) -> str:
    if mode == "probe":
        return derive_probe(template)
    if mode == "restore":
        return derive_restore(template)
    raise ValueError(f"unknown mode {mode!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("probe", "restore"), required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    output = derive(args.template.read_bytes(), args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} ({sha256(output.encode('utf-8'))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
