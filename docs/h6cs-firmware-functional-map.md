# H-6CS functional dissection and modification feasibility — 2026-10-25

## Scope and confidence

We have all2048sequential words of the NY8B062D candidate's documented program
address space. Reset, interrupt, startup and LCD behavior are coherent. This is
strong evidence of the full application, not a verified complete cloning package:
exact silicon, configuration encoding, oscillator trim/calibration and any storage
outside this read window remain unresolved. Reserved words0x7FE/0x7FF are captured
but uninterpreted. Datasheet section5 documents clock/watchdog/etc options without
establishing their placement in this dump.

No hardware interaction or target write occurred during this dissection. The
original dump hash remains unchanged. Derived traces stay in ignored dumps/.

## Concrete routine map (word addresses)

| Address | Function | Evidence/limits |
|---|---|---|
|0000 ->0009|Reset/RAM clearing|FSR setup, bank switching, indirect clear loop|
|0008 ->04FE|Interrupt service|Context save/restore, timer flag and counters, RETIE|
|017C|Application startup|DISI; initializers; LCD; ADC; PWM; timer; ENI|
|018A|Main loop|Watchdog service, flags, state dispatch, ADC and control calls|
|0196..01BE|Ten-state dispatcher|R3E bounds <10; computed jump table01A2..01AB|
|0212..028B|Feedback arithmetic/PWM update|Measurement minus setpoint; accumulation/clamps; final SFUN3|
|028C|Analog channel1 processing|Temporary reference change, sample, lookup conversion|
|04BD|Four-mode indicator output|PB0..2 values and pin directions switched by mode|
|05BC|GPIO setup|PA mask3E, PB maskC7; enables PA0/6/7 and PB3/4/5 outputs|
|05DC|Button debounce and mode advance|PA5 active low; four modes; bounded execution tested|
|06AD|Timer0 setup|TMR0=6, T0MD=3, interrupt enable|
|06B9|ADC setup|R10/R11/R13/R14/R16 configuration|
|06CE|Timer1/PWM1 setup|reloadFF, duty1E, T1CR2=08, T1CR1=83|
|06E2|State transition helper|Sets R3E; clears state counter and elapsed counters|
|0709|ADC sample helper|START/EOC polling twice; combine high/low result bits|
|071C|Table search/conversion|Bounded range00..40, table access through06FA|
|0751|LCD initialization|Four command frames physically matched offline|
|075C|LCD RAM write|101prefix,6address bits, LSB-first payload helper|
|0772|LCD command write|100prefix plus command/don't-care combined framing|
|077E /0788|Serial output|MSB-first / LSB-first bit loops|

Names such as voltage/current/repair/full-charge have NOT been assigned to the
ten state numbers. Clock rate/config must be recovered before converting counter
thresholds into seconds. Arithmetic0x34xx/0x35xx is absent from imported model;
carry-add/subtract interpretation is plausible but not independently established.
No unit conversion to volts/amperes/Celsius is asserted from raw thresholds.

## Ten state handlers

States0..9 dispatch respectively to0677,0693,0439,0669,063C,03AA,065B,0557,
0629,06D8. R3E is the state variable (bank0). R4B is the separate user mode0..3.
Do not conflate charging phases with four user-selected modes.

## Candidate pin/function map

Based on NY8B062D SOP16 only; exact part remains unconfirmed.

| Physical pin | Candidate signal | Firmware evidence | Board correlation |
|---|---|---|---|
|4|PA5|Active-low button at05DC|Matches button/pull-up tracing|
|9|PB4|LCD DATA|Matches measured serial connection|
|10|PB5|LCD WR|Matches measured serial connection|
|11|PA0|LCD CS|Matches measured serial connection|
|12|PA1/AIN1|ADC channel1 at0292|NTC network reported; temperature conversion likely|
|13|PA2/AIN2|ADC channel2 at01CF|Connector network; physical quantity unresolved|
|14|PA3/AIN3|ADC channel3 at01D5|Connector network; physical quantity unresolved|
|15|PA4/AIN4|ADC channel4 at01FC, feeds regulation|Physical quantity unresolved|
|5|PB3/PWM1|Hardware PWM enabled by T1CR1=83; duty updated at028A|Earlier reported NC: contradiction|
|2|PA6|Software-switched output,05_9B and06_4C paths|Earlier reported NC: contradiction|
|3|PA7|State-dependent output|Earlier reported NC: contradiction|
|8/7/6|PB0/1/2|Direction-based four-mode indicator drive|Pin8 LED confirmed;7/6 earlier NC|

The apparently unused pins might reflect obsolete tracing, board variant support,
or a still-unresolved part mismatch. Do NOT rename PWM1 or PA6/PA7 as fan/relay/
charge-enable without tracing destination circuitry. Strong software evidence
cannot establish board connectivity. The most useful later continuity work is
pin2/3/5 to power-board connector and actual fan driver, unpowered.

## Button behavior and actual offline modification demonstration

Bounded execution of original handler05DC, including state helper06E2:
-Active-low polling; first mode change after21consecutive pressed calls.
-Released sample clears debounce counter.
-Mode cycles0->1->2->3->0.
-400additional held calls do not repeat; hold counter saturates250.
-100bursts of10pressed calls separated by released calls never change mode.
-Test initial charging state3 moves tostate1 on accepted press.
-Milliseconds are not established (call scheduling depends on clock/config).

RAM-only proof of modifiability: replace word05E3 from2414 to2405. Same bounded
execution changes first accepted press from21calls to6calls. Both variants pass
expected-event checks. Original file unchanged; NO patched programming image
or write was produced. This is a demonstration, not a recommendation to weaken
real-button debounce. Artifact: analysis/offline-mod-demonstration.json.
Tool: tools/h6cs_ny8_button_trace.py; traces: analysis/button-trace.json.

## Realistic modification targets

Display startup effects, alternate numeric diagnostics, button behavior and mode
selection can now be developed and tested offline. Segment LCD has fixed artwork:
it is not an arbitrary text display. A digit encoding table exists at06C4..06CD;
segment-to-glass mapping still needs confirmation. There are108zero padding words
but these are not a general guarantee of usable patch space or OTP programmability.

Charge thresholds, timing, ADC calibration and thermal behavior are addressable
research targets. They need analog scaling and state semantics first. No charging
bug or faulty threshold has been established in this analysis.

## Can the original be reflashed?

NY8B062D is listed in Nyquest's OTP lineup (2K x14), not flash/MTP. If that identity
is correct, ordinary erase-and-reflash modifications to the used original are not
available. Reading successfully does not imply rewritability. Do not attempt
in-place bit programming as an experiment. A new compatible device, verified MTP
replacement, or small replacement-controller board is the practical mod platform.
No drop-in compatibility or programming support for those alternatives is proven.

## Fan anthem feasibility

A note sequencer is straightforward software. Producing controlled audible tones
from THIS fan is unproven: driver topology, fan wire count and electrical response
are unknown, and no firmware output is yet positively identified as fan control.
Changing PWM frequency might create motor noise; changing RPM is not a reliable
way to synthesize musical pitches. Four-wire fan PWM protocols may specifically
require ultrasonic fixed-frequency control (e.g. Noctua21..28kHz); that example is
not evidence of this charger's fan type.

Never repurpose the identified PWM1 as a musical output until its actual load is
known: firmware evidence suggests it participates in a feedback controller.
A separate piezo driven by a replacement MCU is a predictable route to a short
'Du gamla, du fria' boot tune while preserving independent cooling behavior.
No acoustic behavior, motor modulation, patched image or physical change tested.

## Sources

Nyquest NY8B062D v1.8, pinout p14, program memory p16, SFR tables, PWM1 pp36-37,
configuration section5:
https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf
Official OTP/MTP lineup:
https://www.nyquest.com.tw/upload/2021_09_303/NY8_Lineup_210930.pdf
Opcode model:
https://github.com/jamesw343/Ghidra_NY8A054E
Four-wire fan example, not a specification for the charger's unidentified fan:
https://www.noctua.at/cn/support/faqs/microcontroller-guide-pwm-setup-and-rpm-monitoring

## Executable analysis in graphical emulator

The new emulator/core.mjs NY8 subset also executes selected routines offline:

- Routine071C was checked for all2568-bit inputs against an independent monotonic
 table lookup. Its65-entry table at047C..04BC maps input to index0..64; indices
 are clamped and represent the largest table value<=input (lower bounded at0).
- Isolated mode setup block0444..047B was executed for all four R4B modes.
 Mode0 sets R3B:R3A=281, R35:R34=100 and next state4.
 Mode1 sets256,100,state4; mode2 sets143,65,state4; mode3 sets256,45,state3.
 Physical units/labels remain unknown. This test enters the assignment block
 directly and does not assert real-life entry guard conditions.
- Full startup reaches the physical LCD sequence before stopping at unknown3537
 at0207 under strict opcode handling. Experimental0x34/0x35 interpretation plus
 synthetic ADC/Timer0 runs1,000,000instructions without emulator fault. This is
 not proof of electrical behavior or correct real-time charging regulation.

Replacement part research was interrupted by Nyquest direct datasheet URLs
redirecting to the homepage (NY8BM62D_v1.2, v1.3_SC and NY8BE62D_v1.4). Product
lineup identifies MTP candidates, but no pin/register-compatible replacement was
validated. GUI AVR/STM32 profiles are behavioral porting models, not such claims.

## Segment display and temperature chain reconstructed

Using user photo plus original digit table06C4..06CD, digit bytes can be mapped
as a=bit7,b=3,c=1,d=4,e=5,f=6,g=2. Left/middle/right LCD byte destinations are
nibble addresses16,14,12 respectively. Bit0 at left/middle gives decimal points.
Emulated display routine0013 with R33:R32=2800 produced28.0 and C-bit set in
actual GPIO-derived LCD frames. Exact icon placement remains photograph-derived.

All65temperature indices were tested through the original028C conversion routine,
100calls each, with ADC1=(ROM[047C+temperature+15]&FF)*16. Under explicit
experimental0x34/0x35 semantics the resulting signed R33:R32 is temperature*100
for every point -15..49. Thus firmware formatting strongly identifies this as a
hundredths-of-degree temperature quantity. No physical NTC calibration inferred.

LCD was slow to update because its scheduler requires500Timer0interrupts. The
GUI now has explicit accelerated synthetic timer mode rather than replacing
firmware display data with a fabricated number. Full main-loop execution produces
nonzero LCD RAM and changing outputs. Original GPIO indicator routine04BD tested
for all four modes; mode labels are inferred from left-to-right photograph order.

## System Regis: tested state gates and feedback processing

The current emulator uses manufacturer-assembler-verified ADCAR/SBCAR encodings;
see [CPU audit](h6cs-regis-cpu-audit.md). The following routine tests execute the
original instructions. Register values are deliberately injected for unit tests;
the separate reset/scenario tests exercise complete flow without RAM injection.
Physical input scales and charging-phase names remain unknown.

| Routine | Verified numeric behavior | Evidence boundary |
|---|---|---|
|03F4|ADC2 and ADC3 samples each clamp at1300;50 samples accumulate, outputs are `floor(sum/32)` in R2D:R2C and R31:R30; sets R4D.bit2|Raw arithmetic, not a physical-unit calibration|
|0613|R2D:R2C≥1650 for20 qualifying calls sets R4F.bit1; lower values reset the pending counter; once set the routine does not clear the flag|Main calls it once per completed50-sample window|
|0532|Sets R4D.bit0 when R2D:R2C≥1360 OR R39:R38≥20; when neither holds, an already-set flag clears after1000 calls|The second quantity derives from ADC4; physical meaning unassigned|
|0439 (state2)|Requires both R4E.bit0 and R4D.bit0 before mode setup: modes0/1/2→state4, mode3→state3|All16 combinations of flags and mode tested|
|063C (state4)|Consumes R4D.bit1 events; second event transitions to state5|It counts averaging-ready events, not directly Timer0 ticks|
|057A|Accumulates126 samples of R37:R36 and divides the sum by64 into R39:R38, then sets R4D.bit1|All501 bounded constant inputs tested; see continuation below|

Main-loop ADC4 processing first shifts raw input right once and caps at500.
Main-loop lines01F1–01FA force state0 when R4F is nonzero (and clear PA6).
Consequently state0 can result from a latched input condition; it should not be
called simply "idle" without more evidence. ADC2 default2500 clamps to1300 and
produces2031 after each50-sample block, exceeding1650: this explains the observed
20-window/roughly1000-Timer0-poll transition to state0 in the default simulation.

The nine-case ADC2/ADC3 sweep instead reaches states4and5 when ADC2=0 and ADC3 is
2048or4095. This is a reproducible stimulus experiment, not a valid battery model.
The fixture `tests/fixtures/h6cs/feedback-state5.json` preserves one such case.
No simulated output is connected to hardware.

## Tested ADC4 filter and states5/7/9 (System Regis continuation)

Routine057A is now tested for every bounded sample0..500. It waits for126 samples,
returns `floor(sum/64)`, raises R4D.bit1 and clears accumulator/count. The sum can
reach63000, so this sweep also covers carries into the high accumulator byte.
The highest constant-input output is984. This is a scaled filter, not an ordinary
arithmetic mean or a calibrated ampere value.

The following results are isolated original-routine tests; the outer main loop
can impose other conditions. All counters below are raw values, not seconds.

| State/routine | Tested transition condition |
|---|---|
|5 / 03AA|Five ready-window events with R39:R38 below R35:R34: goes to6 if R27:R26≥60, otherwise7. At equality, the persistence counter clears.|
|5 / 03AA|A ready-window event with feedback<20 goes to7 immediately (subject to earlier branches in the same invocation). Boundary19/20 tested.|
|5 / 03AA|R25:R24≥10800 or R27:R26≥39600 selects8. The routine continues after changing state: a simultaneous ready-window event with feedback19 overwrites8 with7.|
|7 / 0557|Five ready-window events with feedback strictly above reference select4. At equality, persistence clears.|
|7 / 0557|R25:R24≥7200 selects9. Remaining instructions still execute.|
|9 / 06D8→0685|Mode2 and R31:R30<1301 select1; other tested modes or value1301 retain9.|

The state5 timeout precedence is an observed property of the original instruction
sequence, not yet a demonstrated charger defect. Replacing it with an early return
in a port would change behavior. Any safety policy for the new implementation must
make such a choice explicit instead of silently calling it equivalent to the ROM.

The GUI's **Tillstånd & villkor** panel shows the current numeric state, tested
routine conditions, filtered raw values, reference, event counters and flags.
It is read-only commentary on the executing ROM, not a second charging controller.
Unknown states remain labeled as incompletely mapped. No physical units are inferred.
