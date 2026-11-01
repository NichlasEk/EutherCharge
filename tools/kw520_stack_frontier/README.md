# KW520 fixed stack-frontier experiment

This package tests only the fixed cyclic allocations 256, 320, 384, 448, 480
and 512. It does not claim a stack overflow and it never runs the series
automatically. One allocation is completed and reviewed before the next.

## Physical result and closed series

The physical series stopped at allocation 320 on 2026-11-01. Allocation 256
was copied exactly. With allocation 320 active, the display scrolled and the
buttons remained responsive, but the SRAM capture matched only payload bytes
0 through 255 at `0x20003978`. Byte 256 was NUL and the following pre-existing
SRAM structure was unchanged. No cyclic value reached a captured core register
or exception-frame word, so `control_candidate` was false.

Both external-flash sectors were then restored and CRC-verified: pointer sector
`0x003000` returned to `f5c23372`, data sector `0x00c000` returned to the exact
all-FF CRC `f154670a`, status returned to `0x18`, and the final cold start had
normal `Huvudmeny` and responsive buttons. Allocations 384, 448, 480 and 512
must not be run as a continuation of this experiment: the 320 result already
shows that this parser/copy path terminates at 256 bytes and therefore cannot
advance the stack-frontier hypothesis.

The visible bytes use an order-4 De Bruijn sequence over lowercase ASCII and
digits and contain no percent or NUL byte. Four-byte windows are unique through
allocation 512 and do not encode SRAM, internal-flash or peripheral address
ranges. A captured PC/LR
can therefore be mapped back to one exact payload offset without deliberately
supplying a useful execution address.

## One complete allocation gate

Before the first allocation, capture one clean-menu baseline with
`run-baseline.sh --capture-baseline frontier-clean-a`, then cold-start and
require normal `Huvudmeny` again.

1. With normal `Huvudmeny`, install only the inactive data sector:
   `run-data-install.sh --allocation N --write-data`.
2. Cold-start and require normal `Huvudmeny`; then activate it with
   `run-pointer-install.sh --allocation N --activate-frontier-pointer`.
3. Cold-start once. Record display and buttons, whether normal or frozen.
4. Capture SRAM/core/fault state once with
   `run-capture.sh --capture N frontier-N-a`. This freezes the MCU.
5. Without another cold start, restore the pointer with
   `run-pointer-restore.sh --allocation N --restore-frontier-pointer`. This uses GPIO bitbang
   and does not depend on the original firmware's SPI setup.
6. Cold-start and require normal `Huvudmeny` and responsive buttons.
7. Restore the now-unreferenced data sector with
   `run-data-restore.sh --allocation N --restore-data`.
8. Cold-start and require normal `Huvudmeny` and responsive buttons again.

Stop the series immediately when the JSON report has `control_candidate: true`,
the payload is not exact at `0x20003978`, the pointer recovery is not accepted,
or physical behavior differs after final cleanup. Never use J-Link unlock,
unprotect, recover, option-byte writes or mass erase.
