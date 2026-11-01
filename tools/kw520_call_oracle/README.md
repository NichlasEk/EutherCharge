# KW520 MPU-guarded main-flash call oracle

This is an offline-prepared discovery helper, not a firmware dumper. Its only
live candidate command calls one fixed, observed Thumb address with the normal
AAPCS `memcpy(destination, source, 32)` register shape and checks an SRAM-only
result. It contains no internal- or external-flash program/erase sequence.
The current 860-byte binary has SHA-256
`9fb2cb3c8459fdee2980da1d552d1de470dc371e5a7f1c4c03dc6956d097d1a4`.

The helper starts at `0x20001000`. Command 1 only reports `MPU_TYPE`, the prior
`MPU_CTRL`, and the compiled candidate count. Command 2 is rejected unless the
host supplies arm word `0x43414c4c`, the MPU reports at least six regions, and
the candidate index is within the fixed table.

Before a candidate runs, the helper installs an MPU map with no privileged
background region:

| Region | Range | Candidate access |
|---|---|---|
| Main flash | `0x08000000–0x0800ffff` | read/execute |
| Oracle | `0x20001000–0x200013ff` | read/execute |
| Mailbox | `0x20001700–0x200017ff` | read/write, never execute |
| Source | `0x20001800–0x200018ff` | read-only, never execute |
| Destination | `0x20001900–0x200019ff` | read/write, never execute |
| Stack | `0x20002200–0x200022ff` | read/write, never execute |

The candidate runs unprivileged on PSP. No GPIO, SPI, flash controller, PPB,
other SRAM, or external memory range is mapped. Such access should enter the
local fault handler. MPU `PRIVDEFENA` and `HFNMIENA` remain clear. The source,
32-byte destination, return value, two guards, stacked PC/LR, and fault status
are retained in the mailbox. A deliberate UDF after a normal return lets the
privileged fault handler classify exact copy (`0x31`) versus mismatch (`0x32`);
a fault before return is `0xf0`.

The 19 table entries are merely odd main-flash-range values repeatedly found
in 14 SRAM captures. Some are almost certainly return addresses rather than
function entries. Therefore they must never be swept automatically. A future
live procedure must first back up the entire affected SRAM, run command 1 only,
verify the actual MPU region count, and restore SRAM. Each later candidate
requires its own reviewed configuration, timeout, capture, and cold start.

`run-inventory.sh --inventory-only LABEL` is the inventory runner.
It backs up `0x20001000–0x200022ff`, loads and byte-verifies the oracle, runs
command 1, prints the MPU region count, restores VTOR and all 0x1300 affected
SRAM bytes, and requires byte-identical restoration. It never writes the arm
word and has no candidate index/command path. The MCU remains halted afterwards
and requires a cold start.

The end address is deliberate: the oracle stack region is
`0x20002200–0x200022ff` with top `0x20002300`. Bytes above that are part of the
normal firmware's live stack and may change if OpenOCD clears lockup or reports
an external reset during shutdown; they are not written by the oracle and are
excluded from its restoration claim.

Even state `0x31` proves only an SRAM-to-SRAM copy-shaped call. A separate,
explicitly reviewed gate would be required before asking that exact routine to
copy two protected main-flash words. Unlock, recover, option-byte modification,
flash programming, and mass erase remain forbidden.

## Physical inventory result, 2026-11-01

The inventory-only gate ran at 50 kHz SWD with J-Link VTref 3.291 V. The exact
800-byte inventory-version helper readback matched its then-current build hash
`5e12195b946d16c02e8b138eeede04a78a070867689477c9e1605ce7ee932e48`.
Mailbox state `0x10` reported
`MPU_TYPE=0x00000800`, eight regions, prior `MPU_CTRL=0`, candidate count 19,
candidate address zero, `inventory_ok=1`, and `call_guard_ok=1`. No arm word,
candidate call, or protected-flash read was issued.

VTOR returned to `0x08000000`. The complete affected SRAM range
`0x20001000–0x200022ff` matched before and after with SHA-256
`1730c2dbe10678fb0203beaac7c2ae6609435887a18169e3f1e51658f74e2175`.
OpenOCD returned status 1 while clearing the pre-existing lockup and reporting
an external reset. Fifteen bytes changed only above the oracle stack top, at
`0x2000238a–0x200023f6`, where normal firmware uses its live stack; they are
not part of the helper's write set. Structured evidence is in
`artifacts/kw520-jlink/20261101-call-oracle-mpu-inventory.json`.

After normal cold-start recovery was confirmed, one separate candidate runner
was prepared for index 18 only: `run-candidate18.sh
--candidate-18-sram-copy LABEL`. The fixed address is `0x0800ad8f`, selected
because it occurred twice in the same recurrent SRAM structure. That is only a
ranking signal, not proof of a function entry or `memcpy`.

The candidate configuration verifies eight MPU regions and the exact candidate
address before invocation. It captures result/fault data, then unconditionally
disables the MPU, restores VTOR and byte-restores `0x20001000–0x200022ff`.
Exact copy, returned mismatch, contained fault and contained timeout are all
observations; only exact copy with 32 matched bytes and both intact guards can
qualify the candidate. The runner contains no protected-flash source option.

The first candidate-18 attempt did not invoke main flash: state remained
`0x20` and PC stopped at the old `configure_mpu` epilogue because that non-leaf
assembly function had not preserved LR across its `set_region` calls. Helper
readback and the full affected SRAM restoration were exact. The implementation
now uses `push {lr}` / `pop {pc}`; this changed the binary to the current
call implementation. The later detach command and its host-release guard delay
changed the binary again to the current 860-byte hash above.

The corrected retry reached state `0x21`, proving that MPU setup completed and
the branch instruction was issued. The core did not return or enter the local
fault handler. It was observed in unprivileged Thread mode at PC `0x08010000`,
exactly one byte range beyond the MCU's 64 KiB main flash, with PSP
`0x20002300`. Source and both guards were intact and all 64 destination bytes
remained `0xa5`; no copy occurred. VTOR and the affected SRAM range were again
restored exactly, with before/after SHA-256
`1730c2dbe10678fb0203beaac7c2ae6609435887a18169e3f1e51658f74e2175`.

This is consistent with the documented access-protection behavior already seen
when debug power is active. Candidate 18 is not a copy primitive, and a sweep
of the other observed addresses under the same debug condition is stopped: it
would not discriminate function semantics from the FAP execution boundary.
Structured evidence is local at
`artifacts/kw520-jlink/20261101-call-oracle-candidate18.json`.

## Prepared detach-and-run gate

Command 3 uses the same fixed candidate, SRAM buffers, MPU map and arm word as
command 2, but first enters state `0x40` and polls `DHCSR.C_DEBUGEN`. It does not
configure the MPU or branch until the host debugger has actually disabled core
debug. Once `C_DEBUGEN` is zero, it records state `0x41`, installs the MPU,
drops to unprivileged Thread/PSP and calls candidate 18.

`run-detach18.sh --detach-candidate-18-sram-copy LABEL` is a two-session gate.
The first OpenOCD session backs up SRAM, verifies the helper and proves state
`0x40`, then resumes and disconnects. The second session reconnects after one
second, captures mailbox/core/buffers, disables MPU and restores VTOR plus the
exact affected SRAM backup. The second session runs even if the candidate did
not return. No raw timing assumption decides the branch: the target's own
`C_DEBUGEN` observation does. The gate still has no protected-flash source and
does not sweep candidates.

The first detach attempt proved state `0x40`, but ordinary OpenOCD shutdown
left `DHCSR.C_DEBUGEN` set. The helper correctly remained at its poll loop and
candidate 18 was never invoked. Readback reported
`DETACH_OUTCOME debug-never-detached`; VTOR and affected SRAM restored exactly.
The revised arm phase now writes keyed `DHCSR=0xa05f0000`, then DP
`CTRL/STAT=0x40000000` (system power requested, debug power clear), and requires
readback `0xc0000040`. The target waits an additional 2,000,000-loop guard
before configuring the MPU and branching, giving the DP release time to take
effect. A new cold start is required before this revised gate is attempted.

The revised physical run met both release gates: the target left state `0x40`,
DP readback was `0xc0000040`, and mailbox state reached `0x21`. On reconnect,
however, the unprivileged core was again at PC `0x08010000`, with both MSP and
PSP `0x20002300`. It had not returned, entered the local fault handler or
changed the destination. VTOR and the affected SRAM range restored exactly.

This disproves active core-debug/debug-power as the sole explanation for the
earlier result, but cannot distinguish two remaining cases: FAP may retain the
SRAM execution origin after the branch, or `0x0800ad8f` may be a return address
rather than a callable function entry. Blindly sweeping the other observed
addresses cannot distinguish those cases and is stopped. Structured evidence
is local at `artifacts/kw520-jlink/20261101-call-oracle-detach18.json`.
