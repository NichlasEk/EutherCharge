#!/usr/bin/env python3
"""Qualify the fixed KW520 SRAM marker after a runtime SRAM capture."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREPARE_PATH = ROOT / "tools" / "prepare_kw520_stack_exec_probe.py"
SPEC = importlib.util.spec_from_file_location("prepare_kw520_stack_exec_probe", PREPARE_PATH)
PREPARE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARE)
SRAM_BASE = 0x20000000
SRAM_SIZE = 0x4000


def analyze(sram: bytes, stub: bytes) -> dict[str, object]:
    if len(sram) != SRAM_SIZE:
        raise ValueError(f"expected {SRAM_SIZE} SRAM bytes, got {len(sram)}")
    payload = PREPARE.build_payload(stub)
    buffer = PREPARE.BUFFER_ADDRESS - SRAM_BASE
    mailbox = PREPARE.MAILBOX_ADDRESS - SRAM_BASE
    copied = sram[buffer:buffer + PREPARE.COPY_LIMIT]
    observed_mailbox = sram[mailbox:mailbox + len(PREPARE.MAILBOX)]
    exact_payload = copied == payload[:PREPARE.COPY_LIMIT]
    exact_stub = sram[buffer:buffer + len(stub)] == stub
    exact_return = sram[buffer + PREPARE.RETURN_OFFSET:buffer + PREPARE.RETURN_OFFSET + 4] == payload[
        PREPARE.RETURN_OFFSET:PREPARE.RETURN_OFFSET + 4
    ]
    exact_mailbox = observed_mailbox == PREPARE.MAILBOX
    qualified = exact_payload and exact_stub and exact_return and exact_mailbox
    return {
        "format": 1,
        "sram_sha256": hashlib.sha256(sram).hexdigest(),
        "buffer_address": f"0x{PREPARE.BUFFER_ADDRESS:08x}",
        "mailbox_address": f"0x{PREPARE.MAILBOX_ADDRESS:08x}",
        "copied_payload_exact": exact_payload,
        "stub_exact": exact_stub,
        "return_word_exact": exact_return,
        "mailbox_expected": PREPARE.MAILBOX.hex(),
        "mailbox_observed": observed_mailbox.hex(),
        "mailbox_exact": exact_mailbox,
        "control_flow_qualified": qualified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sram", type=Path, required=True)
    parser.add_argument("--stub", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    result = analyze(args.sram.read_bytes(), args.stub.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["control_flow_qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
