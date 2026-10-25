# System Regis continuation — 2026-10-25

Goal remains active: verified digital twin, then open ESP32-C3 implementation.
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

Tests:all38Node tests pass, including state-gate and full-ROM scenarios.
Two Python static decoder tests and Firefox UI pass. See
`tests/h6cs-emulator.test.mjs` for the full suite. Do not rerun
hardware/probe tests while working on emulation.

Next useful software work:
1. Extend tested state graph beyond2/4/5; `docs/h6cs-firmware-functional-map.md`
   now has exact numeric gating and ADC2 high-condition latch behavior.
2. Validate126-sample ADC4 aggregation, R4E.bit0 logic and state5/7/9 handlers.
3. Model remaining peripherals from primary documentation. No watchdog, DAA or
   SLEEP behavior is claimed. Electrical GPIO, actual oscillator/configuration,
   analog reference scaling and interrupt-entry timing remain unresolved.
4. ESP32-C3 architecture is in `docs/euthercharge-esp32c3-architecture.md`; no
   deployable power-stage implementation or physical pin assignment exists.

SDK research (private temporary tools; no installer execution):
- NYASM archive `/tmp/h6cs-nyasm-2.80.zip`, extracted `/tmp/h6cs-nyasm/app`.
- `nyas.exe` runs directly under Mono in bubblewrap with network disabled and
  private `/dev`; only SDK/synthetic-source directory exposed. See audit commands.
- Installer extracted using `/tmp/h6cs-innoextract-build/innoextract`, upstream
  PR210 commit376a13e; old1.9 and PR202 failed. No system installation changed.
- Archive fetched from AT Win's public NYIDE5.90 ZIP via ranged member reads;
  TLS intermediate independently verified; archive CRC checked. All hashes and
  fixture generator documented. Manufacturer binaries stay outside Git.
