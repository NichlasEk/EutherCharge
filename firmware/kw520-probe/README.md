# KW520 SRAM inventory probe

Build with `make -C firmware/kw520-probe` from the repository root.
This is a RAM-only diagnostic, not a bootable Flash image.

The 172-byte program reads an explicit list of device, protection, clock,
GPIO A/B and DMA1-channel-1 registers into address/value pairs at 0x20002108.
Completion is magic 0x4b575031 at 0x20002100 and state 1 at +4.
It does not configure clocks, toggle outputs or write Flash. It uses no stack.

The first hardware run at VTref 3.291 V loaded and verified the code but returned
an all-zero mailbox: execution is NOT qualified. Both overwritten SRAM windows
were restored with OpenOCD verify_image. OpenOCD reported unavailable working
memory during verification; its fallback produced no verification failure.
The core was left halted and needs a physical cold power cycle.

Evidence remains local in build/kw520-board-probe/session-a, including the full
pre-load SRAM snapshot. Original internal Flash was not erased or programmed.
No original firmware backup was obtained. Existing direct, DMA and boot-memory
read attempts were blocked; do not label their zero buffers as backups.

Second hardware run (session-b) PASSED at 3.296 V. Explicit halt after image
verification, transfer delays, MSP/PSP initialization and all five core register
readbacks were added. All readbacks matched; RUN_DHCSR=01010001 showed the core
running, and STOP_PC=20001a2c matched our terminal loop. Mailbox magic/state
passed (BOARD_PROBE ok=1 restored=1). Both touched SRAM windows were restored
and verified. The original Flash remains unchanged. A cold power cycle is
required. These bundled setup changes qualify this launcher but do not isolate
which missing step caused the first attempt to fail.

The fixed session directory refuses reuse. This proves own-code SRAM execution
and register capture, not a working charger, sensor calibration or Flash backup.

Session-b report SHA256:
4073047a3dc9984a95eeabe9279455282c53f89ec5d0b412da8edb019d502161.
The peripheral snapshot was reset-like/clock-gated: APB1EN=APB2EN=0,
DMA channel 1 all zero and GPIOA reads repeated 28000000. It cannot be used as
the original running application's pin map. Next inventory must capture the
live configuration before a watchdog/reset can erase it and explicitly gate
on the previously verified PA8/SPI2 state.

## Early live inventory: passed

`live-inventory.cfg` captures configuration with MEM-AP before loading any code.
First run at 3.291 V completed with LIVE_INVENTORY=1. PA8/SPI2 checks passed
at entry; GPIOA configuration and SPI2 control were unchanged at exit.
Evidence: build/kw520-board-probe/live-a.txt (local).

- GPIOA CFGR=6951ffff, ODT=00009d00; GPIOB CFGR=ab41417f.
- SPI2 CTRL1=00000357; PB13/14/15 are alternate-function pins, AF0.
- PA8 is the previously traced external Flash CS, MCU pin 29.
- PA9 and PB5/6/9/10 are inputs; the four PB inputs have pull-ups.
  They are button candidates, not yet mapped to physical buttons.
- PA10/11/12/15 and PB3/4/7/8/11 are outputs of unknown function.
- PA0..7, PB0..2 and PB12 are analog-mode pins; this does not prove
  all are connected to ADC sensors.
- DMA1 CH1 CTRL=15a1, count=26 hex, peripheral=4001244c,
  SRAM destination=20002380. The ADC sequence and physical scale remain unknown.

This run did not read ADC configuration/data registers or change target memory.
DHCSR=03090000 confirms the familiar attach-induced lockup; cold-start required.
Next useful probe: compare these input bits for one known held button per boot,
and inspect ADC sequence configuration before mapping measurement channels.

## Button UP observation

User held UP during button-up-a capture (3.293 V, LIVE_INVENTORY=1).
GPIOB IDT changed from 00006f68 to 00006f48: only bit 5 went low.
GPIOA IDT, GPIO modes, pulls and output values were unchanged.
This identifies PB5 as the active-low UP candidate from one paired observation;
a released-button return capture was subsequently obtained at 3.293 V:
button-released-a returned GPIOB IDT=00006f68 with LIVE_INVENTORY=1.
Thus PB5 was high -> low with UP held -> high with UP released, confirming
the active-low UP mapping under the tested setup.
Raw register evidence: build/kw520-board-probe/button-up-a.txt and live-a.txt.

## Button ESC observation

User held ESC during button-esc-a (3.295 V, LIVE_INVENTORY=1).
GPIOB IDT changed from released 00006f68 to 0000eb68 (XOR 00008400).
PB10, a pull-up input, went low; PB15, the SPI2 alternate-function data pin,
went high. The PB15 difference is not assigned to the button. GPIO modes,
pulls and output latches were unchanged. ESC is provisionally PB10 active-low;
UP/PB5 remained high. Subsequent button-esc-released-a at 3.291 V passed
LIVE_INVENTORY=1 and returned GPIOB IDT=00006f68. PB10 is therefore confirmed
as ESC, active-low, by the released/held/released sequence.

## Button DOWN: inconclusive first capture

button-down-a at 3.291 V passed LIVE_INVENTORY=1, but GPIOB IDT=0000ef68
differs from released 00006f68 only at SPI2 PB15. All known GPIO input bits
and GPIOA IDT were unchanged. No DOWN pin is identified from this capture.
Repeat with the button held continuously through the complete read; do not
infer PB6 or PB9 by elimination.

Second held-DOWN capture button-down-b also passed the live gate at 3.291 V.
GPIOA IDT=0000dd00 and GPIOB IDT=00006f68 exactly match released inputs.
Two attempts therefore show no held-DOWN change on ports A/B. Stop identical
retries; first establish whether DOWN navigates the normal menu before debug
attach. Other-port, analog/multiplexed input and physical-contact explanations
remain untested, not established causes.

The user subsequently confirmed that DOWN scrolls before the debug read and
the menu freezes during the read. No DOWN mapping is established.

## Button OK/Enter observation

button-enter-a passed LIVE_INVENTORY=1 with GPIOB IDT=00006f28 versus
released 00006f68: only PB6 went low. GPIOA IDT remained 0000dd00.
PB6 is therefore the provisional active-low OK/Enter input; a subsequent
released capture is still required. GPIO configuration and SPI2 checks passed.
DMA1 CH1 MADDR was 200009c0 in this capture (previously 20002380), so its
destination must not be treated as a fixed ADC buffer address.
Evidence: build/kw520-board-probe/button-enter-a.txt (local).

Released confirmation button-enter-released-a passed LIVE_INVENTORY=1 at
3.290 V and returned GPIOB IDT=00006f68, with GPIOA IDT=0000dd00.
The released/held/released sequence confirms OK/Enter on PB6, active-low.
DMA1 CH1 MADDR returned to 20002380. DHCSR=03090000 again indicates lockup
after attach; cold-start is needed before another normal-menu observation.

## Button Repair observation

button-repair-a passed LIVE_INVENTORY=1 at 3.288 V. GPIOB IDT changed from
released 00006f68 to 00006d68: only PB9 went low. GPIOA IDT remained
0000dd00; GPIO configuration, output latches and SPI2 checks were unchanged.
Repair is provisionally PB9 active-low, pending a released return capture.
Evidence: build/kw520-board-probe/button-repair-a.txt (local).
DHCSR=03090000 again indicates attach-induced lockup; cold-start required.

Released confirmation button-repair-released-a passed LIVE_INVENTORY=1 at
3.291 V. GPIOB IDT returned to 00006f68 and GPIOA IDT remained 0000dd00.
The released/held/released sequence confirms Repair on PB9, active-low.
DHCSR remained 03090000; another cold-start is needed for normal operation.

## Extended live inventory (prepared, not yet captured on hardware)

The MEM-AP inventory now includes GPIOC (48000800) and GPIOF (48001400):
CFGR, OMODE, ODRV, PULL, IDT, ODT, MUXL and MUXH. Each port is skipped
unless its existing CRM AHBEN clock bit is enabled (C=19, F=22). Earlier
AHBEN=004e0015 has both bits set, but there is no C/F input capture yet.

ADC1 at 40012400 is read only if APB2EN bit 9 is already set. The explicit
allowlist is CTRL1/2, SPT1/2, OSQ1/2/3 and PSQ. No status or conversion-data
register is read, and no clocks, outputs, ADC settings or memory are written.
These settings can identify configured channels, not their physical functions
or voltages. The debug attach can still lock up the original firmware.

Register sources verified against the manufacturer's headers on 2026-11-01:
- https://github.com/ArteryTek/AT32F421_CMSIS_Driver/blob/main/at32f421.h
- https://github.com/ArteryTek/AT32F421_Firmware_Library/blob/master/libraries/drivers/inc/at32f421_gpio.h
- https://github.com/ArteryTek/AT32F421_Firmware_Library/blob/master/libraries/drivers/inc/at32f421_adc.h
- https://github.com/ArteryTek/AT32F421_Firmware_Library/blob/master/libraries/drivers/inc/at32f421_crm.h

Host Tcl mock checks passed for enabled clocks (24 extra reads), disabled
clocks (zero extra reads), and a rejected device ID (zero extra reads).
Mock execution has no fallback for target-write commands. This validates the
script path, not physical peripheral behavior. Next: cold-start with all
buttons released for an extended baseline, then a separate held-DOWN capture.

### Extended released baseline: captured

extended-released-a passed LIVE_INVENTORY=1 at 3.290 V with all buttons
released. GPIOA/B IDT remained dd00/6f68. GPIOC CFGR=14000000,
IDT=0000a000, ODT=00002000, PULL=0: PC13/14 are outputs.
GPIOF CFGR=0, IDT=000000c0, PULL=00001000: PF6 is an input with a
pull-up and was high; PF7 was also high but has no internal pull configured.
PF6 is a useful candidate to compare, not yet a physical button mapping.

ADC1 CTRL1=00000100, CTRL2=009e0103, SPT1=00e00000,
SPT2=001fffc0, OSQ1=00500000, OSQ2=0, OSQ3=22531062, PSQ=0.
The configured ordinary sequence has six slots: channels 2, 3, 4, 6, 5, 17.
This does not identify external sensor functions or measure their voltages.
DHCSR=03090000: cold-start before the held-DOWN comparison.
Raw evidence: build/kw520-board-probe/extended-released-a.txt (local).

### Extended held-DOWN capture

extended-down-a passed LIVE_INVENTORY=1 at 3.291 V. GPIOF IDT changed
from 000000c0 to 00000080: PF6 alone went low. GPIOA/B/C inputs, all
captured GPIO configuration/output latches and ADC settings were unchanged.
This identifies PF6 as the provisional active-low DOWN input and explains
why earlier A/B-only captures saw no button change. A released return
capture remains pending. DHCSR=03090000; cold-start before that capture.
Raw evidence: build/kw520-board-probe/extended-down-a.txt (local).

Released return extended-down-released-a passed LIVE_INVENTORY=1 at 3.290 V.
GPIOF IDT returned to 000000c0; GPIOA/B/C inputs remained dd00/6f68/a000.
The released/held/released sequence confirms DOWN on PF6, active-low.
ADC configuration remained unchanged. DHCSR=03090000 requires a cold-start
for normal operation. Evidence: build/kw520-board-probe/extended-down-released-a.txt.

### Confirmed physical button mapping

| Button | GPIO | Pressed level |
| --- | --- | --- |
| UP | PB5 | Low |
| OK/Enter | PB6 | Low |
| Repair | PB9 | Low |
| ESC | PB10 | Low |
| DOWN | PF6 | Low |

Each mapping has a released/held/released observation. These establish inputs,
not debounce timing or a validated replacement firmware implementation.
