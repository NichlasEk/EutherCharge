#!/usr/bin/env python3
"""Offline H-6CS Padauk read-protocol workbench. No USB/serial backend.

SPDX-License-Identifier: GPL-3.0-or-later
Protocol adapted from free-pdk/easy-pdk-programmer-software fpdk.c
(Copyright 2019-2020 freepdk), revision cdc40ae65f85c1ed93f304f5008c6b9b6c5c0043.
This file is GPL-3.0-or-later, independently of the repository's MIT license.
No probe, erase, write, calibration or security-option operations are provided.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

WORDS = 0x600
WORD_BITS = 14
READ_FRAME = 0x5A5A5A56
PINS = {"vdd": 1, "gnd": 16, "clock": 13, "data_out": 14,
        "data_in": 3, "vpp": 4}
PROFILES = ("PMC131-S16A", "PMS131-S16")


def read_words(bus, profile, start=0, count=WORDS):
    """Experimental OTP2_2 READ only; deliberately omit upstream write-based ID.

    bus methods: safe_off(), mode(pin, 'input'/'output'), drive(pin, 0/1),
    rail('vdd'/'vpp', millivolts), delay_us(n), sample(pin).
    Backend must independently enforce electrical limits and safe shutdown.
    This is not identification: caller must already know the target protocol.
    Timing follows upstream requested delays, not measured physical timing.
    """
    if profile not in PROFILES:
        raise ValueError("Unsupported/unverified profile")
    if type(start) is not int or type(count) is not int or not (
            0 <= start < WORDS and 1 <= count <= WORDS - start):
        raise ValueError("Read must stay inside the 1536-word program space")

    def send(value, bits):
        for shift in range(bits - 1, -1, -1):
            bus.drive(PINS["data_out"], (value >> shift) & 1)
            bus.drive(PINS["clock"], 1)
            bus.delay_us(1)
            bus.drive(PINS["clock"], 0)
        bus.drive(PINS["data_out"], 0)

    result = []
    bus.safe_off()
    try:
        bus.drive(PINS["clock"], 0)
        bus.mode(PINS["clock"], "output")
        bus.rail("vpp", 5000)
        bus.delay_us(100)
        bus.rail("vdd", 3000)
        bus.delay_us(500)
        bus.mode(PINS["data_in"], "input")
        bus.drive(PINS["data_out"], 0)
        bus.mode(PINS["data_out"], "output")
        send(READ_FRAME, 32)
        for address in range(start, start + count):
            send(address, 12)
            word = 0
            for _ in range(WORD_BITS):
                bus.drive(PINS["clock"], 1)
                bus.delay_us(1)
                bit = bus.sample(PINS["data_in"])
                if bit not in (0, 1):
                    raise ValueError("Invalid sampled bit")
                word = (word << 1) | bit
                bus.drive(PINS["clock"], 0)
            result.append(word)
    finally:
        # Backend safe_off must be idempotent and work after a failed operation.
        # Do not depend on a sequence of possibly failing host commands here.
        bus.safe_off()
    return result


class TraceBus:
    """Pure simulation, always returns zero; never represents a real dump."""
    def __init__(self):
        self.events = []

    def safe_off(self):
        self.events.append(["safe_off"])

    def mode(self, pin, mode):
        self.events.append(["mode", pin, mode])

    def drive(self, pin, value):
        self.events.append(["drive", pin, value])

    def rail(self, name, mv):
        self.events.append(["rail", name, mv])

    def delay_us(self, us):
        self.events.append(["delay_us", us])

    def sample(self, pin):
        self.events.append(["sample", pin])
        return 0


def compare_dumps(paths):
    """Check full raw LE16 captures; agreement is not proof of firmware validity."""
    if len(paths) < 3:
        raise ValueError("Supply at least three independent full captures")
    files = [Path(p) for p in paths]
    if len({(p.stat().st_dev, p.stat().st_ino) for p in files}) != len(files):
        raise ValueError("Repeated paths, symlinks or hardlinks are not independent captures")
    captures = [p.read_bytes() for p in files]
    for data in captures:
        if len(data) != WORDS * 2:
            raise ValueError("Expected 3072 bytes: 1536 little-endian 16-bit containers")
        words = struct.unpack("<1536H", data)
        if any(w >= 1 << WORD_BITS for w in words):
            raise ValueError("Nonzero upper bits in a 14-bit code word")
    same = all(data == captures[0] for data in captures[1:])
    words = struct.unpack("<1536H", captures[0])
    uniform = len(set(words)) == 1
    return {
        "byte_identical": same,
        "uniform_first_capture": uniform,
        "repeatable_nonuniform_capture": same and not uniform,
        "firmware_validated": False,
        "note": "Agreement does not prove identity, unlocked memory or executable firmware",
        "captures": [{"path": str(p), "bytes": len(d),
                      "sha256": hashlib.sha256(d).hexdigest()}
                     for p, d in zip(files, captures)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show verified limitations; no hardware access")
    trace = sub.add_parser("trace", help="Create SIMULATED read waveform events")
    trace.add_argument("--profile", choices=PROFILES, required=True)
    trace.add_argument("--start", type=lambda x: int(x, 0), default=0)
    trace.add_argument("--count", type=lambda x: int(x, 0), default=8)
    trace.add_argument("--output", type=Path, required=True)
    compare = sub.add_parser("compare", help="Audit three or more existing full captures")
    compare.add_argument("files", nargs="+")
    args = parser.parse_args()
    try:
        if args.command == "status":
            print(json.dumps({
                "hardware_access": False, "target_identity": "unknown",
                "experimental_read_profiles": PROFILES,
                "chip_pins_not_zif_positions": PINS,
                "read_rails_mv": {"vdd": 3000, "vpp": 5000},
                "blockers": [
                    "Stock minipro TL866A has no verified Padauk algorithm",
                    "Open-TL866 VPP minimum setting is nominally 9.8V, not 5V",
                    "Upstream OTP probe AND read preflight use WRITE command 0x7",
                    "Direct READ without ID preflight requires known-chip testing",
                    "No validated adapter, rail sequencing, timing or TL866 backend",
                    "YFC4604/PFC460/PMS163 read protocols not implemented"],
            }, indent=2))
        elif args.command == "trace":
            bus = TraceBus()
            read_words(bus, args.profile, args.start, args.count)
            with args.output.open("x") as f:
                json.dump({"simulation": True, "hardware_validated": False,
                           "profile": args.profile, "start": args.start,
                           "count": args.count, "events": bus.events}, f, indent=2)
            print(f"SIMULATION ONLY: {args.output}")
        else:
            report = compare_dumps(args.files)
            print(json.dumps(report, indent=2))
            return 0 if report["repeatable_nonuniform_capture"] else 2
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
