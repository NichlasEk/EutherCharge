# Interrupt and configuration audit — 2026-10-25

Primary reference: [NY8B062D v1.8](https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf), sections2.1,3.15 and3.16.

Corrections: software INT clears GIE before vectoring to0001. R-page INTF reads
are masked by INTE, while stored flags remain latched until firmware changes them.
This also applies through INDF and to read-modify-write instructions. Hardware
interrupt dispatch continues to inspect stored flags and enable bits directly.

Four focused tests verify software INT with pending hardware IRQ, RETIE behavior,
all256 INTE read masks, indirect reads and masked read-modify-write behavior.
These are instruction-boundary semantics; interrupt-entry latency and documented
ENI-immediately-before-RETIE corner behavior are not modeled.

The feedback-state5 and MODE-cycle reports remain equal to their preceding
versions in events, cycles, LCD RAM, first RAM-write timing and bounded PWM trace.
Both retain the48-bit physical startup command match. Reports are in ignored
`artifacts/h6cs-emulator/interrupt-feedback.json` and `interrupt-mode.json`.

## Configuration evidence boundary

The readout manifest describes2048sequential14-bit words and does not claim
configuration coverage. Its reserved final words at07FE/07FF have no verified
bit map. They must not be treated as decoded oscillator/watchdog configuration.
The saved SDK chip profile is binary; a plain-text inspection exposed no usable
watchdog fields. No hardware reads or writes were attempted.

The candidate datasheet gives watchdog periods3.5/15/60/250ms and configuration
choices for enable and reset versus interrupt. Register WDTEN alone therefore
does not determine actual behavior. Prescaler assignment also affects timeout.
Until config is established, no period or reset action is silently selected.

Reproduce tests:

```sh
node --test tests/h6cs-emulator.test.mjs tests/h6cs-gpio.test.mjs tests/h6cs-timing.test.mjs tests/h6cs-interrupt.test.mjs
```

Next useful investigation: inspect manufacturer configuration/profile formats
read-only, or build explicitly parameterized watchdog experiments. Neither path
establishes the original chip's configuration without independent evidence.
