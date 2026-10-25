# GPIO pin-resolution model — 2026-10-25

Primary reference: [NY8B062D v1.8](https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf),
sections3.1.6/7,3.1.11/12,3.1.21,3.3.1–5,3.5 and3.14.2. Exact chip identity and
configuration-word RD_OPT remain unconfirmed.

Port writes update output latches. Input reads sample pin levels. Output reads
select latch or pin according to RD_OPT. The former emulator always overlaid the
button and PWM on latch reads, independent of direction. That old mode remains
available as `legacy`; `latch` and `pad` are explicit configuration hypotheses,
selectable in the UI. Their names do not assign a numeric fuse encoding.

Implemented digital resolution:
- IOSTA/B direction, output latches and external digital drive.
- Active-low internal pull enables; separate PA5 pull-up/pull-down controls.
- PA5 always open-drain; PB selectable open-drain; released outputs can be pulled.
- PB3 PWM selection; PB7/6 remain general register bits.
- Analog-disabled digital paths, selected unsupported alternate functions,
  conflicting strong drives, opposed pulls and floating pins return unknown.
- MODE is modeled as a switch to ground plus an external pull-up on PA5. The
  exact resistance, board routing and electrical behavior are not established.
- LCD receives resolved PA0/PB5/PB4 transitions, including direction changes.
  Unknown serial levels abort the partial frame rather than inventing bits.

Unknown digital reads default to zero; the sensitivity-test selector can instead
fill them with one. Both are deterministic simulation conventions. The
snapshot/UI preserve unknown masks and per-pin reasons; zero is not a predicted
voltage. No analog thresholds, RC, drive strength, crystal/reset mux or GPIO
interrupts are modeled. Buzzer, IR and additional PWM/comparator behavior remain
incomplete. The choice of output read source under an overriding peripheral and
IOST input setting still requires physical validation. This is not a full pad model.

## Evidence

Six focused tests cover direction/read source, pulls/open-drain/button, unknown
states, PWM read versus latch, LCD suppression while pins are inputs, and both
RD_OPT hypotheses running original boot. The existing51 tests continue to apply.
Firefox tests select both pin models and reproduce01 18 28 03 from reset.

Two four-million-instruction runs with `feedback-state5.json` both produce
5,416,320 modeled cycles, no halt, state path0→1→2→4→5 and48matching physical
LCD startup bits. Final unknown masks are PA=0x1e, PB=0x04; these do not make a
physical ADC calibration claim. Reports:
`artifacts/h6cs-emulator/gpio-latch.json` and `gpio-pad.json` (private/ignored).
Agreement in this scenario does not identify RD_OPT or prove all future branches.

Reproduce with the local private ROM and capture paths:

```sh
node --test tests/h6cs-emulator.test.mjs tests/h6cs-gpio.test.mjs
node tools/h6cs_emulator_run.mjs dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin dumps/h6cs-probe/nyquest-v5-post-original-lcd-20261025-01.json 4000000 clocked tests/fixtures/h6cs/feedback-state5.json latch
```

Use `pad` as the final argument for the other hypothesis; use `-` instead of a
scenario path for default inputs. No hardware operations are involved.

## Actual read evidence and sensitivity comparison

CPU operands are now read only when an instruction consumes them. Immediate
instructions and port writes no longer perform a spurious port read. Per-PC
statistics count consumed unknown bits, with masks for bit tests, bit writes,
AND and OR. Indirect reads are resolved to the actual port. This is direct
operand-use instrumentation, **not** transitive taint analysis through RAM/flags.

The4million-step feedback-state5 scenario has7,986 actual port-read instructions;
6,637 consume some unknown bits, all in BSR/BCR read-modify-write operations.
The direct button bit-test at05DC consumes no unknown bit; ANDAR at04C8 also
masks the unknown bits away. The read-modify-write cases preserve other bits in
the same port; this does not establish that those bits can never matter later.

Four runs (latch/pad × unknown0/1) agree on step/cycle counts, state/mode/duty
events, final LCD RAM, first LCD RAM-write time and the final bounded PWM edge
window. A separate1.6million-step MODE scenario agrees on the same comparisons;
it executes the mode cycle including a transient register value4 before wrapping
back to0. No direct bit branch consumes an unknown bit in either tested scenario.

`tools/h6cs_gpio_compare.mjs` checks four reports, matching ROM/capture hashes and
stimuli, completed budgets, LCD startup comparison and non-truncated event lists.
It rejects differences in the compared fields. Reports are under ignored
`artifacts/h6cs-emulator/gpio-evidence-*.json` and `gpio-button-*.json`.

This is evidence for these two input scenarios and two constant unknown-bit
patterns. It is not a proof for all individual bit combinations, changing unknown
levels, full pad traces or physically calibrated analog inputs. The UI exposes
both fill choices and read counts so the convention is visible.

Run the9GPIO tests with `node --test tests/h6cs-gpio.test.mjs`. The headless runner
accepts a final `zero` or `one` argument after the GPIO mode. Invoke the comparator
with the four resulting report paths. Original firmware remains local/unchanged.
