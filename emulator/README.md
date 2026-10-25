# EutherCharge H-6CS emulator

A local graphical reverse-engineering workbench, separate from the existing KW520
Studio. No USB/programmer access. No firmware is bundled or uploaded.

Start from the repository root:

```sh
python tools/serve_h6cs_emulator.py --firmware dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin
```

Open http://127.0.0.1:8766 in Firefox. Click **Ladda labbdump**. Alternatively omit
--firmware and use **Öppna .bin**. Input is2048little-endian14-bit words stored in
4096bytes. Other lengths/upper-bit formats are rejected. Server listens on loopback
only, serves only emulator assets and the explicitly supplied firmware path.

## What works

- NY8 instruction execution, PC/ACC/STATUS, banked RAM, call stack, breakpoints,
  single step, batches and run/pause/reset.
- Local original ROM executes reset and sends the measured LCD command sequence.
- Editable ADC1..4 raw12-bit inputs, active-low button, state/mode and RAM editing.
- HT1621-style serial command and RAM decoding from emulated PA0/PB4/PB5 edges.
  Display is a128-segment RAM matrix. Real segment-to-glass mapping is unknown.
- Optional synthetic Timer0 interrupt source with editable tick interval.
- Explicit experimental switch for inferred0x34/0x35 ADCAR/SBCAR instructions.
- AVR and STM32 porting profiles run an illustrative shared CC/CV system model;
  battery voltage, temperature, faults, current limit and voltage target are editable.
- Export inspection snapshots without ROM bytes. Snapshots are not loadable or
  cycle-exact replay images.

## What is NOT verified

This is a partial NY8-family emulator, not a cycle-accurate NY8B062D implementation.
Exact chip identity remains unknown. Reset defaults, complete interrupt priority,
watchdog behavior, oscillator config, peripheral timing, port electrical behavior,
ADC conversion latency and calibration are not fully modeled. Timer0 is optional
and synthetic. ADC returns immediately. CLRWDT is a no-op, SLEEP stops execution.
Only Timer0 interrupts are modeled. Stack overflow halts rather than wrapping.
Unknown instructions halt before advancing PC. Use the experimental arithmetic
switch only as an explicitly labeled hypothesis; any resulting charging behavior
is not hardware validation. CPU run speed is not real elapsed charging time.

AVR/STM32 profiles are NOT CPU emulators and do not run NY8 binary. They demonstrate
a replaceable-controller architecture and a standalone illustrative control law,
not original charging logic or actual pin/electrical compatibility. Their fan
animation is not evidence of the charger's fan wiring. No programming/write path.

The register/port interpretation is the NY8B062D candidate. ADC physical scaling
is intentionally not guessed in original-ROM mode. R3E state numbers0..9 do not
yet have reliable charging-phase names. Direct RAM edits bypass original helpers
and can make inconsistent state: useful for exploration, not a validated transition.

## Tests

```sh
node --test tests/h6cs-emulator.test.mjs
```

Eight public synthetic tests cover parsing, arithmetic, banked/indirect access,
unknown opcodes, LCD, ADC, stack/timer and model faults. Four additional tests run
when the ignored original dump exists: full boot LCD, one million experimental
instructions, all256inputs to the original lookup routine, and four-mode setup.
Public checkout skips those private tests instead of shipping proprietary firmware.

Opcode masks derive from jamesw343/Ghidra_NY8A054E commit
b057376fc34250ee9aa988aba3f420be61e47fc0 (MIT); license retained in
LICENSE-opcodes.txt. Semantics implemented locally with reference to Nyquest
NY8B062D v1.8. These sources are evidence for a related architecture, not exact
silicon identification. Original code/readout stays in ignored dumps/.

Optional Firefox UI regression (requires Playwright outside this dependency-free
app, local server running with the private dump):

```sh
PLAYWRIGHT_MODULE=/path/to/playwright-core FIREFOX_EXECUTABLE=/path/to/playwright/firefox node tests/h6cs-emulator-ui.cjs
```

Screenshots and the inspection export are saved in ignored artifacts/h6cs-emulator.

## Photo-based segment display (2026-10-25)

The red/black EAFC housing and blue display follow the user's photograph. SVG
segments are rendered directly from emulated LCD RAM, not from the ADC sliders.
Digit bytes occupy RAM nibble addresses16/17,14/15,12/13. The firmware's ten-digit
lookup table establishes segment masks a=7,b=3,c=1,d=4,e=5,f=6,g=2. Bit0 is used
for decimal points on the first two digits. Units/battery at10/11 and season bits
at18/19 are code-derived label hypotheses; exact glass layout is not electrically
verified. Indicator lights use emulated port latches AND direction configuration
from original routine04BD, with physical labels inferred from photograph ordering.

**Labbkörning** explicitly resets and enables inferred carry arithmetic and
synthetic Timer0 at one tick per emulated instruction. It warms up200000steps
then runs continuously. This accelerates original scheduling, not real time.
**Displaytest28.0°C** invokes original indicator/display subroutines with injected
RAM values, producing actual LCD frames for the reference appearance. It is a
subroutine fixture, not a full-device boot or physical temperature validation.

The sensor-temperature slider chooses ADC1 using the65-entry firmware table.
All65points -15..49 were exercised through100calls to the original conversion
routine: R33:R32 equals signed temperature*100 in the emulator, under experimental
carry arithmetic. Physical sensor calibration and real sampling interval remain
unknown. Numeric display output comes from the original formatting/serial code.

16core tests now pass, plus Firefox tests for photo output28.0°C, summer/LED,
temperature→ADC1=2176, accelerated main-loop RAM writes and previous interactions.

### Instruction-clock Timer0

Enable Timer0, then select **Instruktionscykler + T0MD** to use the candidate
NY8B062D clock/prescaler model. The divider input applies only to the synthetic
lab timer. Firmware chooses divide16; LCD updates take many more instructions
than the accelerated lab mode. This mode counts instruction cycles, but omits
interrupt-entry latency and external clocks and is not calibrated to wall time.
The **Labbkörning** button deliberately selects the synthetic fast timer again.
See `docs/h6cs-regis-cpu-audit.md` and `tools/h6cs_emulator_run.mjs` for reproducible
startup comparison and remaining identity/ISA limitations.
