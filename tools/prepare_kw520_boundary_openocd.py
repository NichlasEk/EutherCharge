#!/usr/bin/env python3
"""Derive three fixed boundary-probe gates from the qualified sector gate."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


TEMPLATE_SHA256 = "710926ea8b61331246bb235f1466bf8efc42e2191b2da90774f4b3db211b4704"
OLD_NOOP = "set noop_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x42 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0xf5c23372 && $erased_crc == 0 && $final_crc == 0 && $pages == 0 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0 && $cleanup == 0}]"
OLD_WRITE = "set restore_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x7985c2f6 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]"


VARIANTS = {
    "baseline": {
        "title": "Write the fixed nested-record length-4 baseline into verified padding.",
        "stem": "boundary-baseline",
        "chunk": "baseline",
        "binary": "boundary_baseline",
        "arm": "0x41524d42",
        "label": "BOUNDARY_BASELINE",
        "magic": "0x4b574253",
        "buffer": "0xb461d992",
        "target": "$target_crc == 0xf5c23372",
        "final": "0xb461d992",
        "noop_target": "0xb461d992",
        "accepted": "ACCEPTED: exact boundary baseline programmed and verified",
        "noop": "ACCEPTED: exact boundary baseline already present; no write",
        "refused": "REFUSED: fixed boundary baseline gate did not pass",
        "size": "0x6cc",
    },
    "extend": {
        "title": "Extend only the nested record length from 4 to 8.",
        "stem": "boundary-extend",
        "chunk": "extended",
        "binary": "boundary_extend",
        "arm": "0x41524d43",
        "label": "BOUNDARY_EXTEND",
        "magic": "0x4b574558",
        "buffer": "0xe4e92a7b",
        "target": "$target_crc == 0xb461d992",
        "final": "0xe4e92a7b",
        "noop_target": "0xe4e92a7b",
        "accepted": "ACCEPTED: exact boundary length extension programmed and verified",
        "noop": "ACCEPTED: exact boundary extension already present; no write",
        "refused": "REFUSED: fixed boundary extension gate did not pass",
        "size": "0x6cc",
    },
    "restore": {
        "title": "Restore original sector from either exact boundary test stage.",
        "stem": "boundary-restore",
        "chunk": "original",
        "binary": "boundary_restore",
        "arm": "0x41524d44",
        "label": "BOUNDARY_RESTORE",
        "magic": "0x4b574252",
        "buffer": "0xf5c23372",
        "target": "($target_crc == 0xb461d992 || $target_crc == 0xe4e92a7b)",
        "final": "0xf5c23372",
        "noop_target": "0xf5c23372",
        "accepted": "ACCEPTED: exact boundary-test sector restored and verified",
        "noop": "ACCEPTED: original sector already present; no boundary restore write",
        "refused": "REFUSED: fixed boundary restore gate did not pass",
        "size": "0x6d0",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_exact(text: str, old: str, new: str, count: int) -> str:
    actual = text.count(old)
    if actual != count:
        raise ValueError(f"template token count {actual}, expected {count}: {old!r}")
    return text.replace(old, new)


def derive(template: bytes, mode: str) -> str:
    digest = sha256(template)
    if digest != TEMPLATE_SHA256:
        raise ValueError(f"refusing changed restore template {digest}")
    cfg = VARIANTS[mode]
    text = template.decode("utf-8")
    text = replace_exact(
        text,
        "# Qualify the fixed sector-restoration helper against an already-correct sector.\n"
        "# Accepted result is state 0x42: no Write Enable, erase, or program executed.",
        f"# {cfg['title']}\n# Only exact CRC-gated states are accepted.",
        1,
    )
    text = replace_exact(text, "restore-noop-", f"{cfg['stem']}-", 27)
    text = replace_exact(
        text,
        "build/kw520-format-probe/restore-sector-003000-chunk",
        f"build/kw520-boundary-probe/{cfg['chunk']}-sector-003000-chunk",
        4,
    )
    text = replace_exact(text, "build/kw520-spi-patch/restore_sector.bin", f"build/kw520-spi-patch/{cfg['binary']}.bin", 1)
    text = replace_exact(text, "0x41524d32", cfg["arm"], 1)
    text = replace_exact(text, "RESTORE_NOOP", cfg["label"], 1)
    noop = OLD_NOOP.replace("0x4b575052", cfg["magic"]).replace("0xf5c23372 && $target_crc == 0xf5c23372", f"{cfg['buffer']} && $target_crc == {cfg['noop_target']}")
    write = (
        "set restore_ok [expr {$core_ok && $done && $magic == " + cfg["magic"] +
        " && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == " + cfg["buffer"] +
        " && " + cfg["target"] +
        " && $erased_crc == 0xf154670a && $final_crc == " + cfg["final"] +
        " && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]"
    )
    text = replace_exact(text, OLD_NOOP, noop, 1)
    text = replace_exact(text, OLD_WRITE, write, 1)
    text = replace_exact(text, 'puts "ACCEPTED: fixed restore helper exited before Write Enable"', f'puts "{cfg["noop"]}"', 1)
    text = replace_exact(text, 'puts "ACCEPTED: exact format-probe sector restored and verified"', f'puts "{cfg["accepted"]}"', 1)
    text = replace_exact(text, 'puts "REFUSED: fixed restore no-op gate did not pass"', f'puts "{cfg["refused"]}"', 1)
    text = replace_exact(text, "0x6cc", cfg["size"], 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=tuple(VARIANTS), required=True)
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
