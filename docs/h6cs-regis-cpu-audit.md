# System Regis: CPU and startup audit (2026-10-25)

Current: ADCAR/SBCAR encodings are manufacturer-assembler verified; see the final
verification section. Earlier stop/opt-in notes below preserve the audit baseline.

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

## Clocked ADC follow-up

A separate optional ADC model now implements the v1.8 section3.14.3 conversion
period `(sampling ADC clocks + resolution bits + 2) * ADC clock divider`.
Manufacturer table31 examples (352,15,13,11 instruction clocks) are regression
fixtures. Result packing is currently implemented only for12-bit conversions;
8/10-bit result modes stop explicitly rather than assuming alignment.

It checks ADEN/GCHS, clears EOC while busy, completes ADR/ADD atomically, sets ADIF
and supports enabled ADC interrupt dispatch. START reads zero and result fields
resist firmware writes. The sample is latched at START as a simulation choice.
Unsupported channels or overlapping START requests stop execution. Disabling ADEN
cancels a pending conversion in this model; physical cancellation behavior has not
been measured. Analog settling, reference-voltage scaling and the256us bias startup
requirement are not modeled. No clock frequency is assumed to turn cycles into seconds.

The runner now defaults to clocked ADC; pass `instant` as the fourth argument after
the instruction budget for comparison. UI controls expose both modes. The photo
fixture and accelerated lab button explicitly restore instant ADC. Earlier audit
statements about absent ADC timing describe the baseline before this follow-up.

Measured offline follow-up (`regis-run-clocked.json`,4million instructions):
5,415,542 modeled instruction cycles;1,348 Timer0 interrupts;18,307 ADC
conversions. First LCD RAM frame completes at instruction1,484,052 / cycle2,009,983.
At the default raw stimuli, observed state progression is0→1→2→0; these numeric
states must not yet be labeled charging phases. First LCD update with instant ADC
was at instruction1,707,386 / cycle2,010,114: similar cycle count but substantially
different instruction count is consistent with the firmware's ADC polling loops.

A new regression operates MODE through the main loop and Timer0 polling, with no
routine jumps or RAM injection. Separate presses traverse0→1→2→3→0, and holding
continues without repeat. This validates modeled firmware button behavior, not a
physical debounce time or verified charging-mode thresholds.

## Replayable external-input scenarios

The runner accepts an optional JSON scenario after its ADC mode argument:

```sh
node tools/h6cs_emulator_run.mjs \
  dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin \
  dumps/h6cs-probe/nyquest-v5-post-original-lcd-20261025-01.json \
  1300000 clocked tests/fixtures/h6cs/mode-cycle.json
```

Actions are ordered instruction indices plus raw ADC1–4 values and/or button level.
Unknown fields, invalid samples and actions outside the execution budget are
rejected. No scenario action changes RAM, PC or hardware. Reports include applied
stimuli with modeled cycle counts as well as observed state/mode/duty changes.

The MODE fixture produces stable0→1→2→3→0 through actual firmware execution. The
instruction trace also exposes the intermediate value4 between INCR at05E7 and
CLRR at05EB before wraparound; that is an implementation detail, not a fifth user
mode. Scenario indices are reproducible execution positions, not calibrated time.

## Independent manufacturer assembler verification — current status

The earlier inferred-carry limitation is now resolved for instruction encoding.
NYASM2.80(Build251121.00), invoked for NY8B062D, generated3537 for
`SBCAR 0x37,0`, exactly the original strict-mode stop word. It generated3420/34A0
for ADCAR R20 with accumulator/register destination and3537/35B7 for SBCAR R37.
All96 general-purpose register operands, both destinations and both instructions
were assembled without diagnostics:384 independent golden encodings. They support
masks FF00/3400 and FF00/3500. Arithmetic and Z/DC/C semantics remain grounded in
manufacturer instruction descriptions and are exhaustively regression-tested for
all byte pairs and both carry inputs. No opcode opt-in is needed anymore.

`tests/fixtures/h6cs/nyasm-carry.json` contains only words generated from our own
synthetic source, not charger firmware. `tools/h6cs_nyasm_fixture.py --source PATH`
generates that source; `--listing PATH` verifies the resulting listing and emits
its SHA256 plus cases. SDK software is not committed or redistributed.

Source: [AT Win's published Nyquest tooling](https://www.atwin-tech.com/download/edownload.html),
NYIDE5.90 bundle, member `NYASM 2.80 [Build 251121.00].zip`.
Archive SHA256:8044754429fb013fa9376566a595ec9901e60c416746461e61c8dd4729946a22.
`nyas.exe` SHA256:31a59fb0b090da7ad6fc7419cad6c5ffe2fa1ee2f2c48ae519de22b0c5109698.
`Nyquest.Assembly.dll` SHA256:aabbd7c4dadd753682204a836150fd000d6519b228a26512fec6ca57195dbd30.

The bundle member was retrieved with verified TLS and checked against its ZIP CRC.
The server omitted an intermediate certificate; that intermediate was independently
verified against the system trust store before use in a temporary CA bundle. No
system trust settings were changed. Innoextract PR210 at376a13e unpacked the installer
without executing it (older local and PR202 extractors did not handle this package).
Mono ran `nyas.exe -p NY8B062D -l --human-read-error carry-gpr.asm` inside bubblewrap
with no network, private `/dev`, and only SDK/test files exposed. No programmer,
original dump or target hardware was available to the assembler.

Reproduction pattern after obtaining/extracting the SDK:

```sh
python tools/h6cs_nyasm_fixture.py --source /path/to/sdk/app/carry-gpr.asm
# Run only nyas.exe, not NYIDE or a writer. An isolated Mono command was used:
bwrap --unshare-net --ro-bind /usr /usr --ro-bind /etc /etc \
  --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 \
  --dev /dev --proc /proc --tmpfs /tmp --bind /path/to/sdk/app /work \
  --chdir /work --setenv HOME /tmp \
  /usr/bin/mono /work/nyas.exe -p NY8B062D -l --human-read-error carry-gpr.asm
python tools/h6cs_nyasm_fixture.py --listing /path/to/sdk/app/carry-gpr.lst
```

This confirms encodings on the selected assembler target, not the physical chip's
model. It also does not fill gaps in ADC electrical behavior, WDT, GPIO or timing.
The fresh `regis-run-verified-isa.json` records continued execution beyond the old
strict-mode stop, with the physical48-bit LCD comparison still passing.

## Feedback-input exploration

Nine reset runs,4million instructions each, clocked ADC and instruction Timer0,
ADC1=1500/ADC4=300, no button or RAM injection, gave:

| ADC2 raw / ADC3 raw |0|2048|4095|
|---|---|---|---|
|0|state0|state5|state5|
|2048|state0|state0|state0|
|4095|state0|state0|state0|

The state5 cases passed0→1→2→4→5; other cases passed0→1→2→0.
`tests/fixtures/h6cs/feedback-state5.json` preserves one discriminating input case.
It is a regression target for modeled firmware, not a physical charging recipe.
No raw ADC value is labeled volts or amps. Reports are under ignored
`artifacts/h6cs-emulator/sweep/` with input hashes and events.

A scan of20 existing `*lcd*.json` captures found45 command frames and no complete
RAM-write candidate. Therefore there is no available measured post-startup glass
trace to claim as a match; acquiring one would require separately approved hardware
work. Further software work can still map state transitions and missing peripherals.
