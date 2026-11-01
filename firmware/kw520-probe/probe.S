.syntax unified
.cpu cortex-m4
.thumb
.section .text,"ax"
.global probe_start
.thumb_func
probe_start:
  cpsid i
  ldr r0, =0x20002100
  movs r1, #0
  str r1, [r0]
  ldr r2, =registers
  add r3, r0, #8
1:
  ldr r4, [r2], #4
  cbz r4, 2f
  ldr r5, [r4]
  str r4, [r3], #4
  str r5, [r3], #4
  b 1b
2:
  movs r1, #1
  str r1, [r0, #4]
  dsb sy
  ldr r1, =0x4b575031
  str r1, [r0]
3:
  b 3b
.align 2
registers:
  /* Configuration and input registers only: no output or clock writes. */
  .word 0x40015800, 0x4002201c
  .word 0x40021000, 0x40021004, 0x40021014, 0x40021018, 0x4002101c
  .word 0x48000000, 0x48000004, 0x48000008, 0x4800000c
  .word 0x48000010, 0x48000014, 0x48000020, 0x48000024
  .word 0x48000400, 0x48000404, 0x48000408, 0x4800040c
  .word 0x48000410, 0x48000414, 0x48000420, 0x48000424
  .word 0x40020008, 0x4002000c, 0x40020010, 0x40020014
  .word 0
