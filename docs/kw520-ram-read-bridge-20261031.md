# KW520 RAM-based internal firmware read bridge

## Purpose and present evidence

The preferred extraction route is not an SRAM-to-SPI bridge. It is a 308-byte
Cortex-M4 helper that executes from SRAM, reads bounded pieces of the MCU's own
64 KiB program-flash address range, and exposes each piece in a 1 KiB SRAM
buffer for J-Link/MEM-AP retrieval. External SPI flash is only a fallback sink.

Corrected-power testing has already established stable, byte-identical reads of
all 16 KiB SRAM and a successful one-word SRAM write/read/restore. That proves
the transport can place the helper, but does not yet prove either SRAM code
execution or internal-flash visibility while debug protection is active.

## Deliberately separated gates

1. Halt the already locked-up core and inspect PC/SP without changing SRAM.
2. Back up the complete SRAM work window, load 308 bytes, read them back and
   compare byte-for-byte while the core remains halted.
3. Redirect SP/PC to SRAM and require mailbox magic `KWRP`, state `1`.
4. Request only two words at `0x08000000`; accept state `0x11` and two returned
   words, or record the local fault state `0xf0` and stop.
5. For each full read, repeat the load/readback and alive gates from a cold
   start. Only after the host has compared the helper readback byte-for-byte,
   request 64 independently checked 1 KiB chunks covering
   `0x08000000–0x0800ffff`.
6. Restore VTOR and the entire SRAM code/mailbox/buffer/fault-stack window,
   cold-cycle target power, then repeat the complete acquisition independently.
7. Combine a dump only if all 64 chunks have exact size and the two 64 KiB
   acquisitions are byte-identical. The checker also requires the loaded helper
   readback to match its build, the full SRAM restore to match its backup, and a
   plausible Cortex-M initial SP/reset vector. Record SHA-256 and inspect the
   disassembly before calling it firmware.

The helper has no code for option bytes, flash controller unlock, erase,
programming, or external-flash writes. Its chunk command rejects zero length,
more than 256 words, and any source outside the internal 64 KiB range.

## Prepared artifacts

- Source: `tools/kw520_ram_probe/probe.S`
- Linker layout: `tools/kw520_ram_probe/linker.ld`
- Reproducible build: `make -C tools/kw520_ram_probe`
- Binary: `build/kw520-ram-probe/probe.bin`, 308 bytes
- Binary SHA-256:
  `abc47fdb82ec7dd17fdf6e11166e1973341cb092382d2c60d6a2149a460f5663`
- Gate configurations: `build/kw520-jlink-20261031/cortex-halt-gate.cfg` and
  `ram-probe-{load,exec,flash,full-dump}.cfg`
- Offline assembler/checker: `tools/kw520_ram_probe/assemble_dump.py`

No internal firmware has yet been obtained. A successful build, SRAM write, or
mailbox response must not be promoted to a verified firmware dump. The final
claim requires two identical full reads.

## Live gate 1 result

With the target supplied only by the user's external 3.3 V backfeed, J-Link
measured VTref at 3.290 V and read DPIDR `0x2ba01477`. The Cortex-M4 target was
successfully placed in debug halt: state `halted`, PC `0x00000000`, SP
`0x20003b90`, XPSR `0x20000003`, DHCSR `0x00030003`. XPSR exception number 3
matches the previously observed HardFault path; this gate proves that the core
can nevertheless be halted. It did not load SRAM, read internal flash, reset,
unlock, erase, or program anything. Evidence:
`artifacts/kw520-jlink/20261031-ram-probe-halt-gate.json`.

## Live gates 2–4 result

After a fresh target power cycle, gate 2 backed up `0x1400` bytes and loaded the
308-byte helper. Its MEM-AP readback matched the build exactly, SHA-256
`abc47fdb82ec7dd17fdf6e11166e1973341cb092382d2c60d6a2149a460f5663`.
Gate 3 then proved actual SRAM execution: PC stopped in the helper loop at
`0x20001066`, and the mailbox contained magic `0x4b575250` with alive state 1.

Gate 4 requested exactly two words from `0x08000000`. The helper completed with
state `0x11` and count 2, but returned `0x00000000, 0x00000000`. Those are not
plausible Cortex-M initial-SP/reset-vector values. The full acquisition was not
run. VTOR was restored to zero and all `0x1400` backed-up SRAM bytes matched
their restoration readback exactly, SHA-256
`258040a55efc585da1d0d85ce7741ca0b9279d2a1e1006b429482cced742bf89`.
DP sticky flags and both power requests were cleared; final CTRL/STAT was
`0x00000040`.

This result matches section 5.5.1/table 5-5 of Artery's AT32F421 reference
manual: with access protection enabled, main Flash reads are prohibited in
debug mode and when booting/executing from SRAM or boot memory, while execution
from main Flash retains read permission. Consequently an address alias does not
turn this helper into a full readout path. The next extraction route must keep
the MCU executing from main Flash, such as a carefully demonstrated parser/
update-path disclosure, or use a separately qualified fault-injection route.
Disabling FAP remains forbidden because the transition mass-erases main Flash.

Evidence: `artifacts/kw520-jlink/20261031-ram-probe-gates-2-4.json`.
