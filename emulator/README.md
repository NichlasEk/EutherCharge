# EutherCharge H-6CS emulator

Local graphical reverse-engineering workbench, separate from KW520 Studio.
No USB/programmer access. No firmware is bundled or uploaded.

```sh
python tools/serve_h6cs_emulator.py --firmware dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin
```

Open http://127.0.0.1:8766 in Firefox and click **Ladda labbdump**. Alternatively
omit --firmware and use **Öppna .bin**. Input is2048little-endian14-bit words in
4096bytes. The server listens on loopback and serves emulator assets plus the
explicitly supplied dump. Original firmware remains in ignored dumps/.

## Controls and execution

The NY8 instruction model provides run/pause, stepping, breakpoints, banked RAM,
PC/ACC/STATUS, stack inspection, raw ADC1–4 inputs and an active-low MODE button.
State(R3E), user mode(R4B) and RAM can be edited, bypassing firmware helpers;
these deliberate edits may create inconsistent state.

Carry opcodes ADCAR/SBCAR are enabled normally. Their384 GPR encodings were
independently assembled with NYASM2.80, and arithmetic/flags are exhaustively
tested. There is no longer an experimental-opcode checkbox. Unsupported opcodes
still stop explicitly. This validates encoding, not physical MCU identity.

**Timer0** offers a synthetic lab clock or instruction cycles with the candidate
NY8B062D T0MD prescaler. The divider input applies only to synthetic timing.
**ADC** offers instant results or clocked12-bit conversion with EOC and interrupts.
Clocked samples are latched at START; unsupported channels/modes stop explicitly.

**Labbkörning** resets and selects synthetic Timer0 at one tick per instruction,
instant ADC and200000warmup instructions, then runs continuously. This accelerates
scheduling, not real time. For a documented-clock run, select instruction Timer0
and clocked ADC, enable Timer0, reset, then run. The original main loop produces
LCD RAM frames after roughly1.5million instructions with the default stimuli.

**Displaytest28.0°C** invokes original indicator/display routines with injected
RAM values. It is a formatting fixture, not a full startup or physical measurement.
The temperature slider selects raw ADC1 values using the firmware's65-entry table;
-15..49°C conversion is regression-tested but physical NTC calibration is unknown.

AVR/STM32 profiles run a separate illustrative CC/CV model. They do not emulate
those processors or run the NY8 binary. Their fan animation does not identify the
original fan wiring. State export omits ROM; it is not a reloadable replay image.

## Display evidence

Red/black EAFC housing and blue LCD follow the user's photograph. SVG segments
come from firmware-generated LCD RAM. Digit bytes use nibble addresses16/17,
14/15,12/13. The ROM digit table establishes a=7,b=3,c=1,d=4,e=5,f=6,g=2.
Decimal points use bit0 of the first two bytes. Unit/battery and season labels
remain provisional glass mappings. LEDs follow port latch/direction combinations
from routine04BD; physical label ordering is inferred from the photograph.

All48 complete captured startup command bits match instruction-generated output.
No full electrical timing or post-startup display trace match is claimed.

## Limits and provenance

This is a partial NY8 model, not a cycle-exact digital twin. Exact chip identity,
oscillator configuration, interrupt-entry latency/priority, complete reset state,
WDT, GPIO electrical behavior, PWM waveform and analog calibration remain open.
SLEEP and DAA still stop rather than guessing behavior. CLRWDT updates status
flags but has no watchdog timebase. Stack overflow stops instead of wrapping.
Modeled interrupts are Timer0 and clocked ADC completion. CPU speed is not elapsed
charging time. Numeric states0..9 do not yet have validated charging-phase names.

Most opcode masks derive from jamesw343/Ghidra_NY8A054E commit
b057376fc34250ee9aa988aba3f420be61e47fc0(MIT); LICENSE-opcodes.txt is retained.
Carry encodings additionally have manufacturer-assembler evidence in
`tests/fixtures/h6cs/nyasm-carry.json`. Semantics use NY8B062D v1.8 documentation.
See `docs/h6cs-regis-cpu-audit.md` for chronological evidence and remaining gaps.

## Regression tests

```sh
node --test tests/h6cs-emulator.test.mjs
python tests/test_h6cs_ny8_static.py
PLAYWRIGHT_MODULE=/path/to/playwright-core FIREFOX_EXECUTABLE=/path/to/firefox node tests/h6cs-emulator-ui.cjs
```

38Node tests pass with the local dump, plus Python static-analysis and Firefox UI
tests. Private-ROM cases skip when the dump is absent. Browser tests require the
local server and private dump. Reports/screenshots remain in ignored artifacts/.
`tools/h6cs_emulator_run.mjs` compares capture bits and replays external ADC/button
scenarios without RAM injection; see `docs/h6cs-emulator.md`.
