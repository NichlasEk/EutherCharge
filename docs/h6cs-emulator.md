# Graphical H-6CS emulator

Entry point: emulator/index.html; instructions and model limits: emulator/README.md.
Local server: tools/serve_h6cs_emulator.py, loopback port8766. Optional private
firmware route serves only the explicitly supplied4096-byte file. No USB access.

First version offers original-ROM NY8 execution with instruction stepping,
breakpoints, banked RAM/state editing, ADC injection, button, GPIO-derived LCD
frames/segment RAM, optional synthetic Timer0 and explicit inferred-opcode switch.
AVR/STM32 switches select standalone behavioral porting profiles, not instruction
emulators; their adjustable CC/CV/fan logic is illustrative and separate from ROM.

Validation:12Node tests passed, including four private-ROM tests (LCD startup,
1million experimental instructions, exhaustive256input lookup, four mode setups).
Firefox GUI testing covers local loading, strict unknown halt, state/RAM edits,
experimental mode, family profiles, injected fault, mobile layout, breakpoints
and state download. Screenshots/logs in ignored artifacts/h6cs-emulator/.

Private firmware remains ignored and unchanged; no copied dump in web assets,
no commit/push or hardware operation performed. Inspectable state export omits
ROM contents; it is not a reloadable replay snapshot.

## System Regis audit

See [CPU audit](h6cs-regis-cpu-audit.md) for identity evidence, flag/reset fixes,
short-branch corrections, the optional instruction-clock Timer0, and the offline
capture-comparison runner. The suite now contains 24 passing tests with the private
ROM available. Baseline emulator and analysis were committed as 69762ac; earlier
text above describes initial bring-up rather than the current versioning state.
