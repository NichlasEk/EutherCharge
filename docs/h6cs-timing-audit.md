# Instruction timing audit — 2026-10-25

Primary references:
- [NY8B062D v1.8](https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf),
  section3.6 and instruction table36/details.
- [NY8A054E v1.5](https://www.nyquest.com.tw/upload/2024_11_293/NY8A054E_v1.5.pdf),
  section3.1.3 and instruction descriptions, used only as shared-ISA reference.
  Its ADC-less register map still contradicts the charger's peripheral usage.

## Correction and bounded verification

Assigning Prescaler0 to Timer0 with T0MD must leave the prescaler cleared after
that instruction. The emulator previously cleared it before the instruction and
then advanced it again when Timer0 was running. It now also clears at instruction
completion. Clearing before advancement still prevents interpreting an old large
phase as multiple ticks under a newly smaller divisor. Exact subcycle ordering
of peripheral writes is not established by this instruction-boundary model.

Four timing tests check this postcondition and the following complete divisor
period, changing divisor without fictitious accumulated ticks, fixed instruction
costs (calls/branches/returns/TABLEA/INT included), and taken/untaken skips. They
supplement the67existing tests. These tests do not establish physical oscillator
frequency or interrupt-entry latency.

## Original instruction usage

`tools/h6cs_timing_audit.mjs` executes a supplied ROM and validated input scenario,
counts instructions/cycles, records PCL-write sites and T0MD writes, and measures
modeled gaps between CLRWDT instructions. Reports include the ROM hash, budget,
scenario and explicit limitations; no ROM words are printed.

The feedback-state5 scenario runs4million instructions using38opcode families,
5,416,320 modeled cycles and5,082CLRWDT instructions. PCL is written5,082times
at word address01A1, where MOVAR R02 selects the state dispatch table. Thus PCL
write timing is relevant; it is not an unused corner case. WDTEN is set throughout
this run, but watchdog clock and configuration behavior remain unverified. First
CLRWDT completes at cycle1324; the largest observed steady gap is3711modeled
cycles (ending at instruction2969517). The last clear is at cycle5415319, so the
trailing observation window is1001cycles. These are not microseconds or a proven
watchdog safety margin.

The available instruction tables list MOVAR as1cycle and generic descriptions say
program branches take2. No explicit PCL-destination timing exception was located.
The existing1cycle MOVAR behavior is retained; no extra cycle is guessed from PIC
similarity. Hardware cycle evidence or a manufacturer simulator is still needed.

One T0MD write occurs at06B2 (step1103) with value03. The observed original run
configures Timer0 while disabled, so this correction preserves its opcode totals
and cycle count. It fixes a model rule, not an observed charger failure.

Reproduction:

```sh
node --test tests/h6cs-emulator.test.mjs tests/h6cs-gpio.test.mjs tests/h6cs-timing.test.mjs
node tools/h6cs_timing_audit.mjs dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin 4000000 tests/fixtures/h6cs/feedback-state5.json
```

Current report: `artifacts/h6cs-emulator/timing-audit.json`. A local older A054E PDF
was incomplete; a fresh direct download also timed out and is retained with a
`.partial` suffix. The complete manufacturer document was read through the web
PDF parser instead. Do not use the truncated local PDF as evidence.
