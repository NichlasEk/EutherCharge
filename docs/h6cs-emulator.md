# Graphical H-6CS emulator

Run `python tools/serve_h6cs_emulator.py --firmware <private-4096-byte-dump>` and
open http://127.0.0.1:8766. The loopback server exposes emulator assets and only
the explicitly supplied firmware file; there is no USB interface. See
[emulator README](../emulator/README.md) for controls and model limits.

The NY8 model executes the original ROM with stepping, breakpoints, banked RAM
editing, raw ADC injection, MODE button, GPIO-derived LCD frames and segment RAM.
The face follows the supplied EAFC photo. The28.0°C display fixture deliberately
injects state and invokes original formatting code; it is not a full startup test.
AVR/STM32 profiles are separate illustrative behavioral models, not CPU emulators.

Timer0 can use a synthetic lab clock or instruction cycles with the candidate's
T0MD prescaler. ADC can return instant lab samples or use a clocked12-bit
conversion model with EOC polling and completion interrupts. The accelerated lab
button deliberately selects synthetic timing. ADCAR/SBCAR encodings now have independent NYASM2.80 assembler evidence and
run without an opt-in. NY8A054E is not an established chip identity;
the observed ADC block instead supports a B062D-like peripheral model.

## Verification

- `node --test tests/h6cs-emulator.test.mjs`:34 tests, including exhaustive CMPAR
  flags, clock/ADC examples, private-ROM startup, conversion table, mode settings,
  complete main-loop MODE cycling, and display writes from reset.
- `python tests/test_h6cs_ny8_static.py`: dynamic short-branch analysis regression.
- `tests/h6cs-emulator-ui.cjs`: Firefox integration test for loading, debugger,
  RAM editing, timer/ADC selectors, photo display, family profiles, faults, mobile
  layout, breakpoint and state export. Playwright/Firefox paths may be supplied
  with PLAYWRIGHT_MODULE and FIREFOX_EXECUTABLE.
- `tools/h6cs_emulator_run.mjs`: offline report with input hashes, direct comparison
  of48 measured LCD command bits and generated bits, state/mode/PWM events and
  optional replayable ADC/button scenarios. See the [CPU audit](h6cs-regis-cpu-audit.md)
  for commands and exact evidence boundaries.

Private-ROM tests skip when the ignored dump is unavailable. Local artifacts,
captures and screenshots are under ignored `artifacts/h6cs-emulator/`. Original
firmware is neither bundled with the application nor committed. State exports omit
ROM contents and are inspection snapshots, not reloadable replay files.

The hardware-backed match is startup command content only. Full electrical timing,
analog calibration, watchdog behavior, physical power regulation and exact MCU
identity are unverified. [ESP32-C3 architecture](euthercharge-esp32c3-architecture.md)
defines a simulation-first replacement plan; it is not deployable charger firmware.
