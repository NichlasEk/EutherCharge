# System Regis continuation — 2026-10-25

Goal remains active: verified digital twin, then an open replacement implementation; MCU choice is now open.
No hardware has been accessed in this development session. Original dump hash
remains4b8f241e38f60983267cf0f2de480d9c93e3d9766aefab901aef6e2afb615784.
Do not assume NY8A054E identity: its ADC register map contradicts the firmware;
NY8B062D-like peripherals are the current model, not a proven exact chip.

Git uses `.git-local`; main branch. Existing programmer research changes and
HANDOFF.md were dirty before this session and remain outside scoped commits.
Emulator/analysis commits:69762ac,50a72c3,1fea69e,5fa75ca,4da858f,9d58c20.
No push performed. Subsequent state-gate documentation/tests follow these commits.

Local server remains http://127.0.0.1:8766, serving the explicitly selected private
dump. Reload Firefox to receive current UI. No build step or frontend dependencies.
Playwright module `/tmp/h6cs-playwright-core/package`; Firefox binary
`/home/nichlas/.cache/ms-playwright/firefox-1543/firefox/firefox`.

Current implementation and reproduction commands: `docs/h6cs-emulator.md`,
`emulator/README.md`, `docs/h6cs-regis-cpu-audit.md`. Independent assembler evidence
removed the carry-opcode gate. The regular CPU executes beyond PC0207/word3537.
Clocked ADC and instruction-clock Timer0 reach display RAM writes from reset.
The complete measured48startup command bits match; no physical LCD RAM-write trace
was found among20existing LCD captures. Do not equate this with full hardware proof.

Artifacts: `artifacts/h6cs-emulator/regis-run-verified-isa.json`,
`regis-run-clocked.json`, `regis-mode-cycle.json`, `sweep/summary.json` and reports.
Four-million-step verified-ISA run:5,415,542 cycles,1,348 Timer0 IRQs,18,307 ADC
conversions,81,150 carry instructions, no halt. Strict20,000-step run also no halt.
First LCD RAM frame at step1,484,052/cycle2,009,983 for default clocked stimuli.

Tests:all71Node tests pass (51core plus16GPIO plus4timing), including state-gate and full-ROM scenarios.
Two Python static decoder tests and Firefox UI pass. See
`tests/h6cs-emulator.test.mjs` for the full suite. Do not rerun
hardware/probe tests while working on emulation.

Next useful software work:
1. Prioritize emulator fidelity over port implementation, per latest user steering.
   Numeric state handlers0–9 and R4E.bit0 qualification now have routine-level tests;
   whole-loop scenario coverage and physical meanings remain incomplete.
2. Timer1/PWM now runs from original SFUN writes and has a live waveform panel.
   See `docs/h6cs-timer1-model.md` for source, conventions and limitations.
3. Resolve peripheral gaps: GPIO electrical mux/direction, watchdog, DAA/SLEEP,
   oscillator/configuration, analog scaling and interrupt-entry timing. External
   Timer1 edges, PS1CV, buzzer/comparator mux remain unimplemented.
4. Obtain a physical LCD RAM/PWM reference only after separately approved hardware
   work. Current measured comparison remains the48startup bits.
5. MCU selection and5V adaptation are open. The ESP32-C3 architecture document
   now records this. Portable feedback code is an offline differential reference,
   not deployable charging control.

Latest run: `artifacts/h6cs-emulator/regis-timer1.json`,4million instructions,
5,415,542 modeled cycles,21,149 Timer1 underflows, no halt, LCD48bits match.
Firefox verifies the new PWM panel as well as previous UI flows. The C++ reference
matches20,051 ROM-driven filter/condition updates, including internal accumulators.
Run `node tests/h6cs-feedback-differential.mjs` with the private ROM available.

SDK research (private temporary tools; no installer execution):
- NYASM archive `/tmp/h6cs-nyasm-2.80.zip`, extracted `/tmp/h6cs-nyasm/app`.
- `nyas.exe` runs directly under Mono in bubblewrap with network disabled and
  private `/dev`; only SDK/synthetic-source directory exposed. See audit commands.
- Installer extracted using `/tmp/h6cs-innoextract-build/innoextract`, upstream
  PR210 commit376a13e; old1.9 and PR202 failed. No system installation changed.
- Archive fetched from AT Win's public NYIDE5.90 ZIP via ranged member reads;
  TLS intermediate independently verified; archive CRC checked. All hashes and
  fixture generator documented. Manufacturer binaries stay outside Git.

Continuation added read-only UI state inspection,42Node tests and state5/7/9
regressions. Firefox also verifies current-state highlighting and profile hiding.

## GPIO continuation

GPIO models `legacy`, `latch` and `pad` are available in the UI and headless runner.
`docs/h6cs-gpio-model.md` records source, explicit uncertainty masks, tests and
four-million-step comparison. Both RD_OPT hypotheses reach state5 with identical
state transitions and LCD startup bits for the feedback-state5 fixture. Do not
infer a verified fuse setting from this agreement. Legacy remains the default;
GPIO electrical thresholds and physical calibration remain unresolved.
Next useful work: propagate uncertainty to actual consumed input bits / branch
sensitivity, extend GPIO interrupts and cover button/full-loop scenarios under both
read-source choices. Preserve numerical-state versus physical-phase distinction.

## GPIO read evidence continuation

Added lazy actual operand reads and per-PC unknown-bit consumption, plus zero/one
sensitivity selection in UI/headless execution. Four configurations agree for both
feedback-state5 (4million steps) and MODE cycle (1.6million steps). Unknown reads
are confined to port BSR/BCR in these runs; no direct bit branch consumes unknown
bits. See `docs/h6cs-gpio-model.md` and `tools/h6cs_gpio_compare.mjs` for exact scope.
No transitive taint proof or physical waveform verification is claimed. Next useful
emulator work is GPIO interrupt behavior and remaining instruction/peripheral gaps;
these tested input scenarios do not justify treating unknown inputs as identified.

## GPIO interrupt continuation

Pin-mode GPIO now implements PAB/INT0/INT1 flags, edge selection, priority and
INTE/GIE dispatch. Reset AWUCON/INTEDG corrected toFF/05. PWM output override is
excluded from input-change detection. See GPIO model document for sampling limits.
Original scenarios leave GPIO interrupts disabled: MODE is polled, with8button
edges observed but no GPIO IRQ dispatched. Existing state/LCD/PWM behavior remains
unchanged. Next prioritize original-used gaps (instruction timing, watchdog/config,
ADC calibration and longer state scenarios); GPIO IRQs were a completeness gap,
not an observed original-firmware blocker. No hardware operations performed.

## Timing audit continuation

T0MD now leaves Prescaler0 cleared after the assignment instruction, as documented.
Original feedback-state5 execution is unchanged because it configures Timer0 while
disabled. `tools/h6cs_timing_audit.mjs` inventories actual opcode use, PCL writes and
CLRWDT gaps. PCL state dispatch at01A1 and CLRWDT both execute5,082times in4million
steps. PCL extra-cycle behavior is unresolved; retain current1cycle MOVAR pending
better evidence. WDTEN is set, making watchdog/configuration analysis a useful next
step. See `docs/h6cs-timing-audit.md`. No hardware accessed.
