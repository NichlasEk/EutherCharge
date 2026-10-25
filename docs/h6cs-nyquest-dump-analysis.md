# Original MCU readout: offline code validation, 2026-10-25

The repeated dump contains coherent NY8-family machine code. Strongest evidence:
bounded execution of its LCD initializer reproduces all48bits of the four LCD
command frames previously captured physically, in the same order. This validates
more than opcode recognition or nonuniform data. No hardware operation was
performed in this analysis turn.

## Data distribution

-2048 14-bit words stored as4096bytes (little-endian16-bit containers).
-1940 nonzero words,108zero words (94.73% nonzero).
-844distinct word values;32distinct64-word blocks.
-All108zeros form a single tail region at word addresses0x792..0x7FD.
-Two remaining nonzero words at0x7FE/0x7FF fall in the candidate's documented
 reserved region; their meaning is not established, do not interpret as code.
-Two independent full captures match every raw byte and decoded word.

## Code evidence

Opcode masks sourced from jamesw343/Ghidra_NY8A054E, commit
b057376fc34250ee9aa988aba3f420be61e47fc0. Only the declarative masks are parsed;
no external executable was run. Instruction semantics checked against Nyquest
NY8B062D v1.8. Related-core opcode model does not identify exact chip model.

-Reset vector0x000 jumps to0x009: FSR setup, bank switching, indirect RAM clear
 loop, subroutine initialization, and jump to0x17C startup.
-Hardware interrupt vector0x008 jumps to0x4FE: accumulator/status/FSR save,
 interrupt-flag checks and timer-related code.
-Startup at0x17F calls LCD initializer0x751.
-ADC helper at0x709 uses R10 bit6 START and polls bit5 EOC, then reads R11/R12.
 This agrees with candidate ADMD/ADR/ADD register mapping.
-1996/2048words recognized by imported model.52unknowns all have upper byte
 0x34/0x35; the model explicitly leaves ADCAR/SBCAR unimplemented. Missing-model
 explanation is plausible, but these opcodes have NOT been assigned by guess.
-Linear opcode coverage counts tables/padding too; it is not executable coverage.
 Static conditional reachability is incomplete at unknown/computed operations.

## LCD match to independent physical capture

Initializer0x751 sends four constants through0x772. The command sender emits
four prefix bits1000 then eight bits of each already shifted command byte.
The combined12-bit frames match the previously observed100 +8command +1don't-care:

| Command | Meaning | Reconstructed bits |
|---|---|---|
|01|SYS EN|100000000010|
|18|RC 256K|100000110000|
|28|BIAS1/2,4COM|100001010000|
|03|LCD ON|100000000110|

The bounded interpreter ran actual dump instructions, recording DATA at WR rising
edges while CS was low.440instructions per run. Eight initial-state variations
(carry0/1 and RAM fill00/55/AA/FF) all matched all four measured frames exactly.
This is functional offline evidence, not full-chip emulation or a new physical
measurement. Comparison source: nyquest-v5-post-original-lcd-20261025-01.json.

Firmware writes PA0=CS, PB5=WR, PB4=DATA under the candidate register mapping.
NY8B062D SOP16 maps these to physical11/10/9 respectively: all three agree with
board continuity measurements. This substantially strengthens NY8B062DS16 or a
closely compatible NY8 variant as identification; no exact device ID yet.

## Artifacts and limitations

Private artifacts: dumps/h6cs-nyquest-20261025/analysis/{analysis.json,
disassembly.txt,lcd-trace.json,sources.json,NY8A054E.slaspec}.
Tools: tools/h6cs_ny8_analyze.py and tools/h6cs_ny8_lcd_trace.py.
Original binary hash remains4b8f241e38f60983267cf0f2de480d9c93e3d9766aefab901aef6e2afb615784.
No raw firmware published. Existing dump and captures unchanged.

Latest live post-full-read LCD attempts did not decode clock bits; that separate
capture issue remains. This offline match uses the earlier successful physical
capture, not those attempts. No assertion of current full charging functionality.
Exact chip identity, config semantics and charging algorithm still require work.

Sources:
https://github.com/jamesw343/Ghidra_NY8A054E
https://www.nyquest.com.tw/upload/2023_03_013/NY8B062D_v1.8.pdf
