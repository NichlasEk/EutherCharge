# System Regis: CPU and startup audit (2026-10-25)

## Identity is not established by a successful read protocol

The recovered 2048-word image is reproducible. The chip model is still unknown.
NY8A054E is the programming-protocol and opcode-reference part, not an identified
silicon marking or returned ID. The present peripheral model is NY8B062D-like.

Manufacturer sources:

- [NY8A054E v1.5](https://www.nyquest.com.tw/upload/2024_11_293/NY8A054E_v1.5.pdf),
  printed pp.17–19: R-page 0x10–0x14 are unassigned. There is no ADC register block.
  Page20 specifies short CALL/GOTO high address bits from PCHBUF.
- [NY8B062D v1.8](https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf),
  pp.26–28: ADMD, ADR, ADD, ADVREFH and ADCR at those addresses;
  pp.31–35: Timer0 and F-page controls; p.59: Timer0; pp.87–93: instruction behavior.

The original routine 0x0709 starts conversion in R10, waits for EOC, and combines
R12 and the low nibble of R11. Routine 0x028C uses channel1 and the ROM conversion
table. This is consistent with the B062D ADC block and contradicts an A054E model
with those addresses unassigned. It is not unique proof of B062D: another compatible
ADC-bearing NY8 device remains possible. Do not rename the target to a proven part.

## Implemented corrections

- CMPAR updates Z/C, preserving DC and other flags; exhaustive byte-pair tests.
- CLRWDT sets /TO and /PD. A running watchdog is still absent.
- PCON1 reads reflect the global interrupt latch. IOST cannot enable GIE.
- Candidate reset values restored for PCON, pull controls, directions, PCON1 and
  T0MD. Unspecified X values and RAM still have deterministic zero seeds.
- Short CALL/GOTO obtain their page from PCHBUF, as documented for A054E.
  B062D's table lists long branches; short encodings remain shared-ISA references.
- Instruction cycles count ordinary instructions, taken skips, branches, TABLEA,
  returns and software INT. Computed-PCL writes and interrupt-entry latency still
  require investigation; these counters do not establish cycle-exact execution.
- Optional instruction-clock Timer0 uses T0MD prescaler assignment and division,
  T0EN, overflow flags and existing Timer0 IRQ dispatch. T0MD writes assigning the
  prescaler to Timer0 clear its phase. External/low-speed clocks are unsupported.
- Synthetic Timer0 remains explicitly separate for accelerated UI exploration.

DAA semantics are not fully specified by the available example and remain a hard
stop; SLEEP wakeup, WDT timing, ADC timing, GPIO electrical resolution and PWM
waveform generation are not yet implemented. ADCAR/SBCAR encodings 0x34xx/0x35xx
remain opt-in inferences, even though their arithmetic behavior matches the manual.

## Reproduce the evidence

```sh
node --test tests/h6cs-emulator.test.mjs
node tools/h6cs_emulator_run.mjs \
  dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin \
  dumps/h6cs-probe/nyquest-v5-post-original-lcd-20261025-01.json \
  4000000 > artifacts/h6cs-emulator/regis-run.json
```

The runner hashes both private inputs, compares complete measured LCD command
frames to instruction-generated frames, and records state/mode/PWM duty changes.
It starts at reset, without RAM injection, and reports its assumed opcodes and
limitations. Output contains no ROM bytes. Instruction budget and initial ADC
stimuli are recorded. Private dumps are required; tests skip private cases when
absent, while the runner fails if its supplied input is missing.

The strict CPU reproduces all 48 captured command bits (01,18,28,03), then stops
at unverified word3537 at PC0207. This is hardware-backed **command content**
evidence, not a timing or full-startup match. The physical capture has a trigger
boundary and nominal timing; its first incomplete frame is deliberately excluded.

The experimental CPU also reaches LCD RAM writes through the main loop using
instruction-clock Timer0 with firmware-selected T0MD=3 (divide16). This removes the
need for an arbitrary accelerated timer for that result. It does not remove the
opcode/ADC/reset assumptions or establish calibrated charger timing.

No programmer, charger or power-stage access was performed by these tools.
