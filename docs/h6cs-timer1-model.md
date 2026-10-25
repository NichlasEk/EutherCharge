# Timer1 and PWM1 model — 2026-10-25

Source: [NY8B062D v1.8 manufacturer datasheet](https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf), sections3.4.1–4 and3.7, figures17/18.
This is a candidate peripheral model, not confirmation of physical chip identity.

Implemented in `emulator/timer1.mjs`:10-bit downcounter, reload and one-shot,
prescaling/bypass, TMR1 readback, current high counter bits in TMRH, buffered duty
and reload, underflow flag/interrupt and PWM1 PB3 selection/polarity. Duty and
reload updates latch at underflow while running. The counter traverses zero;
period is reload+1 ticks. UI shows a bounded256-edge trace in modeled instruction
cycles, not Hz or an oscilloscope capture. Export includes peripheral state.

Original routine06CE writes reload255, duty30, prescaler bypass and control83.
Executing it produces256-cycle periods with30 active ticks in the model. A test
executes this actual routine, then advances the peripheral in isolation. Full-ROM
4million-step execution separately preserves the physical48-bit LCD match.

## Explicit limitations

- One-shot follows figure17, which shows1023 frozen after underflow; accompanying
  prose describes stopping at zero. This ambiguity needs physical verification.
- Compare count<duty follows figure18 and documented pulse-width behavior.
- CPU register writes take effect at the start of the modeled instruction;
  prescaler configuration resets phase as a convention. Subcycle timing and
  interrupt-entry latency are not verified.
- External clock mode is gated without injected edges. PS1CV readback, buzzer,
  comparator priority and full electrical GPIO resolution are not implemented.
- Datasheet requires duty≤reload. Out-of-range configurations are not validated
  against hardware and must not be used as a reference for replacement design.
- Actual oscillator/configuration and physical PWM destination remain unknown.

No programmer, original chip or power electronics was accessed.
