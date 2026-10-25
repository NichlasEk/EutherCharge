# Explicit watchdog experiments — 2026-10-25

Source: NY8B062D v1.8 section3.15 (local candidate datasheet; exact MCU identity
remains unconfirmed). The SDK configuration decoder is separate: no original
config block has been established and no settings are automatically imported.

`emulator/watchdog.mjs` starts unconfigured. Experiments must explicitly supply:

```json
{"enabled":true,"action":"reset","baseUs":3500,"instructionHz":2000000}
```

The model counts rational instruction time without rounding fractional milliseconds,
uses the documented base periods and reset/interrupt prescaler ratios, observes
WDTEN, handles CLRWDT and prescaler reassignment, clears /TO at expiry and sets
WDTIF for interrupt mode. INTE/GIE dispatch handles WDTIF alongside existing IRQs.
Snapshots include settings, elapsed credit, prescale count, clears and timeouts.

Reset mode stops with an explicit reset-request diagnostic. It does not execute a
fabricated cold-reset sequence. SLEEP, oscillator drift, subinstruction timing,
watchdog reset register retention and phase behavior across runtime-disable periods
are unverified. Runtime-disable currently freezes elapsed credit as a convention.
The separate WDT/prescaler bookkeeping is an instruction-level approximation; it
is not an electrical clock-domain model.

## Original-ROM sensitivity experiment

Same feedback-state5 stimuli,3.5ms reset timeout, two assumed instruction clocks:

| Assumed instruction Hz | Executed instructions | Modeled cycles | Result |
|---:|---:|---:|---|
|1,000,000|1,486,585|2,013,294|One timeout; explicit reset-request stop|
|2,000,000|4,000,000|5,416,320|No timeout; full budget completed|

These are alternative assumptions, not inferred physical clocks. The first
experiment is intentionally a failure probe. The second does not establish
physical watchdog safety. Reports and explicit JSON assumptions are in ignored
`artifacts/h6cs-emulator/watchdog-*-run.json` and `wdt-*.json`.

Reproduce by appending the assumption file to the timing audit:

```sh
node tools/h6cs_timing_audit.mjs dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin 4000000 tests/fixtures/h6cs/feedback-state5.json artifacts/h6cs-emulator/wdt-2000000.json
node --test tests/h6cs-watchdog.test.mjs
```

Eight focused tests cover expiry boundaries, masked flags/IRQ dispatch, CLRWDT,
all prescaler ratios, configuration/runtime gating, reset stop, all base periods
and prescaler reassignment. The85-test combined suite passed before two additional
watchdog tests were added; all8watchdog tests then passed. Existing original-ROM
regressions pass with the default unconfigured watchdog. No hardware accessed.

## Interactive experiments

The NY8 UI now exposes a separate watchdog panel. Form edits are drafts; only
“Starta om med dessa antaganden” validates and applies them to a new run. Regular
Reset preserves the active assumptions, while loading a ROM, the accelerated lab
shortcut and the display-only test create a fresh unconfigured watchdog. The
status line always reports active settings, not uncommitted form values.

A requested watchdog reset disables Run/Step/Burst. The CPU also refuses further
steps after its debug halt text is cleared, so the GUI cannot accidentally bypass
the missing reset sequence. Explicit experiment restart is required. Invalid input
leaves the existing CPU and its elapsed state unchanged. Snapshots export actual
watchdog configuration and reset-request state.

`tests/h6cs-watchdog-ui.cjs` verifies draft/apply separation, timeout controls,
exported settings, invalid-input preservation, reset and profile visibility in
Firefox. The deliberately low1000Hz test clock is a fast timeout-injection case,
not a physical clock hypothesis. Ten watchdog tests now cover the model/UI helper.
