# KW520 debug connection isolation — 2026-10-31

User observations apply to menu/button responsiveness only, not charging qualification.

## Important wiring correction

The user later found that the J-Link voltage-reference connection had been on
the wrong point and reported that it likely shorted the board toward ground.
Therefore the freeze/HardFault trials in the table below cannot be used as
evidence that normal SWD debug-power activation freezes this MCU or that flash
protection caused the fault. They remain a record of what was observed under
the faulty connection and must be repeated from the corrected baseline.

After correcting the connection, a new raw DPIDR-only trial measured VTref at
3.291 V and returned DPIDR `2ba01477`, ACK 1 and valid parity. It made no DP/AP
write, reset, debug-power request or target-memory access. Evidence:
`artifacts/kw520-jlink/20261031-raw-dpidr-corrected-wiring.json`.

The target was then supplied from a stable external 3.3 V source, with VTref
measured at 3.290–3.293 V. The corrected isolation ladder reproduced the
boundary: DPIDR/status reads, unpowered AP reads and system-power-only requests
left the menu responsive; adding `CDBGPWRUPREQ` changed CTRL/STAT from
`c0000040` to `f0000040` and froze it. The frozen core reports `S_LOCKUP`,
active HardFault and forced escalation. Two corrected snapshots differed in the
specific bus-fault bit (`STKERR` versus `IBUSERR`) but both recorded `INVSTATE`.
Clearing debug/system requests does not resume execution; a complete target
power cycle does. This supersedes the earlier faulty-wiring causal uncertainty.

A corrected-power peripheral inventory found only SPI2 clocked and enabled.
SPI2 CTRL1 is `0x357`: master, mode 3, MSB first, clock divisor 8 and software
chip-select. PB13/PB14/PB15 are alternate-function 0 and match the datasheet's
SPI2 SCK/MISO/MOSI mapping. PB12, the hardware SPI2_CS pin, is analog. PB11 is
an adjacent GPIO output high and is the strongest software-CS candidate, but
continuity or signal activity is still required before any GPIO write. Evidence:
`artifacts/kw520-jlink/20261031-corrected-power-spi-inventory.json`.

Two complete 16 KiB SRAM captures under corrected power were byte-identical,
SHA-256 `254a6cbf37cb7d4a9e3d3518bbd050b5e6bc85413fb97fc76f8663fec8f1b90c`.
The longest zero-filled run was `0x200009fc–0x2000236b`. One aligned word in
its middle, `0x200016b4`, was read as zero, written as `0xa55a3cc3`, read back,
restored to zero and read back again in one session. This proves bounded SRAM
write/read/restore through MEM-AP under the active protection state. It does not
yet prove SRAM code execution or external-flash access. Evidence:
`artifacts/kw520-jlink/20261031-corrected-power-sram-write-restore.json`.

| Trial | Register evidence | User-observed menu |
| --- | --- | --- |
| Raw SWD selection and DPIDR | 2ba01477, valid parity | Responsive |
| Additional DP status read | 00000000 | Responsive |
| Debug power request alone | write10000000, read30000000 | Frozen |
| Debug request set then cleared | 0 -> 30000000 -> 0 | Still frozen |
| Status snapshot while frozen | DHCSR03090000, ICSR803, CFSR21000, HFSR40000000 | Already frozen |
| AP0 ID without power requests | 00000000 with valid protocol ACK/parity | Responsive |
| System power request alone, then AP0 ID | statusc0000040; AP ID0 | Responsive |

The frozen snapshot indicates core lockup, active HardFault, forced fault escalation, stack bus fault and invalid execution state. It was read after OpenOCD reactivated debug/system power; fault ordering and original cause remain unknown. This is not an ordinary debugger halt. A relationship to flash protection is plausible but unproven.

Raw experiments use a local libjaylink harness instead of OpenOCD initialization. The latter asserts both debug and system power requests. No experiment erased/unlocked/programmed flash or issued a target-reset command. AP-ID experiments access debug-port registers, not target CPU memory. Raw harness source and logs are in ignored build/kw520-jlink-20261031; structured results are in artifacts/kw520-jlink/.

The recorded DP state from the old wiring was: system-power request asserted,
debug request clear and SELECT=f0. It is not the current corrected-wiring state.
Normal memory access from the corrected baseline has not yet been tested.

Additional system-only test: AP0 CSW also returned00000000, with valid ACK/parity and unchanged DP statusc0000040. No CSW write or target-memory access. UI observation pending. Latest SELECT=0. Zero readback may reflect an inaccessible/gated AP rather than meaningful register contents.
