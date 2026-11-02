# KW520 probe handoff — 2026-11-01

## Resume here

Goal: develop our own KW520 firmware by mapping the existing board. Preserve
the original internal firmware until an explicit destructive-unlock decision.
Internal firmware has NOT been backed up. No flash/option-byte changes were
made in this probe sequence. This is not a flash-ready charger implementation.

Latest attempt `clamps-joined-adc-b` failed the live-configuration gate; no ADC
RAM was read. User was asked to separate the clamps and cold-start. That
physical action has NOT yet been confirmed. Last confirmed clamp state was
joined, mains/battery disconnected, logic-only supply; user measured 0.052 V
between separated clamps earlier. Last VTref was 3.298 V. Do not infer that
the device has recovered or that the supply arrangement has changed.

## Repository and delivery

Use `git --git-dir=.git-local --work-tree=.` on branch `main`.
Remote: https://github.com/NichlasEk/EutherCharge.git.
Commit `6bc7003` was pushed successfully: six files in `firmware/kw520-probe`,
including the RAM probe, live MEM-AP inventory and confirmed button mapping.
Later ADC-window additions and clamp findings in `live-inventory.cfg` and
`README.md` are still uncommitted, as is this handoff. HANDOFF.md has earlier
uncommitted work too. Many unrelated worktree changes exist: do not stage all.
Raw logs and binaries remain local under `build/kw520-board-probe/`.

## Verified hardware findings

AT32F421C8T7, Cortex-M4; J-Link serial 69401338, SWD 50 kHz.
All five buttons have released/held/released observations, active-low:

| Button | GPIO |
| --- | --- |
| UP | PB5 |
| DOWN | PF6 |
| OK/Enter | PB6 |
| Repair | PB9 |
| ESC | PB10 |

PA8 is the previously traced external SPI flash CS (MCU pin 29).
PB13/14/15 are SPI2 alternate-function pins. Unknown outputs have not been
actuated. GPIOC PC13/14 are configured outputs; their roles remain unknown.

Own stackless RAM code successfully ran in session-b, returned its mailbox,
and both overwritten SRAM windows were restored and verified. The earlier
session-a failure is superseded by that execution result, but the session-b
peripheral snapshot was reset-like and cannot map running original firmware.
The 172-byte build SHA256 is
`e7f72e2efaa2aa9ef3de9b9a0678b078f0d7e9541304a8528cf0a96ce78af988`.
`make -C firmware/kw520-probe` reproduced it before commit.

## Current read-only inventory

`firmware/kw520-probe/live-inventory.cfg` gates on device ID 50020100,
PA8 output-high, PB13..15 alternate function and SPI2 CTRL1=0357.
It reads GPIO A/B plus clock-enabled C/F and ADC configuration only.
No clock enable, output write, ADC trigger or ADC status/data read occurs.
Debug attachment nevertheless disrupts the protected original core; normal
menu operation generally requires a physical cold-start afterward.

Optional `capture_adc_ram 1` checks DMA CTRL=15a1, PADDR=4001244c,
word-aligned MADDR and a complete 48-byte window within 16 KiB SRAM.
It reads that window twice with count bracketing and a final pointer check.
This is not a full buffer-length determination or an atomic snapshot.
Tcl mocks passed valid, invalid-pointer and wrong-device paths.

ADC ordinary sequence is configured as [2,3,4,6,5,17]. Mapping six successive
RAM halfwords to those channels is provisional, not independently verified.
No physical sensor function or voltage scale is established.

## Clamp experiment results

User requested testing joined clamps with only logic power. A first attempted
read was rejected by automatic review until the user supplied 0.052 V; the
subsequent narrowly scoped reads were approved. No workaround was used.

All successful captures had unchanged digital inputs (A/B/C/F:
dd00/6f68/a000/00c0), unchanged ADC configuration and MADDR=20002380.
Means of six raw slots, each over eight values from two windows:

| Local capture label | Slot 1 | Slot 2 | Slot 3 | Slot 4 | Slot 5 | Slot 6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clamps-open-adc-a | 1.875 | 58.375 | 0 | 397.875 | 0 | 1507.25 |
| clamps-joined-adc-a | 2.375 | 61.375 | 0 | 397.875 | 0 | 1580.875 |
| clamps-open-adc-b | 2 | 58.25 | 0 | 400.125 | 0 | 1534.125 |

Slot 6 fell on separation but did not return to the first baseline. This is
not proof of short detection: boots, settling, supply and buffer phase remain
confounders. The first open sample had no explicit fresh cold-start confirmation.
DMA counts and RAM values changed within each successful capture even while
DHCSR=03090000 showed core lockup.

Attempting another joined sample without restarting failed:
`clamps-joined-adc-b.txt`: GPIOA CFGR/ODT=28000000, GPIOB CFGR=0,
SPI2 CTRL1=0, DEVICE_ID=50020100, DHCSR=03090000, LIVE_INVENTORY=0.
No ADC RAM read occurred. These invalid/reset-like values do not prove a
physical reset or a clamp effect. DMA activity during one attachment does not
guarantee valid access on the next. Do not retry identical attaches blindly.

## Next steps

1. Confirm clamps separated and cold-start recovery before more hardware work.
2. Preserve current logs; check actual USB/device state before connecting.
3. Improve the sampling method before more clamp cycles. A bounded single
   attachment with multiple timed snapshots and explicit operator markers
   could avoid reconnect/boot confounders, but is not implemented or qualified.
   Keep identity/state gates and stop on invalid state. No output actuation.
4. Verify DMA layout/channel phase and separate internal channels from physical
   sensing before assigning a clamp-voltage/current input. Do not infer a
   charge-output control pin from ADC correlation.
5. Integrate confirmed button mapping into our RAM probe. Display, sensing,
   inhibit and power-stage mapping/qualification remain outstanding.

Existing command pattern (use a fresh label; do not run until hardware ready):

```sh
timeout 20s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -c 'set capture_label UNIQUE-LABEL; set capture_adc_ram 1' \
  -f firmware/kw520-probe/live-inventory.cfg
```

Replace UNIQUE-LABEL with lowercase letters/digits/hyphens. Existing output
files are intentionally not overwritten. USB execution may require sandbox
approval; do not reuse stale USB bus/device numbers or bypass a rejection.
