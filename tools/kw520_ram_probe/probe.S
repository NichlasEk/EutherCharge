.syntax unified
.cpu cortex-m4
.thumb

.equ MAILBOX,      0x20001700
.equ BUFFER,       0x20001800
.equ STACK_TOP,    0x20002300
.equ FLASH_BASE,   0x08000000
.equ FLASH_END,    0x08010000
.equ SCB_VTOR,     0xe000ed08
.equ SCB_CFSR,     0xe000ed28
.equ SCB_HFSR,     0xe000ed2c
.equ SCB_MMFAR,    0xe000ed34
.equ SCB_BFAR,     0xe000ed38
.equ MAGIC,        0x4b575250  /* "KWRP" */

.section .vectors, "a", %progbits
.align 7
.global probe_vectors
probe_vectors:
  .word STACK_TOP
  .word probe_start + 1
  .word probe_fault + 1 /* NMI */
  .word probe_fault + 1 /* HardFault */
  .word probe_fault + 1 /* MemManage */
  .word probe_fault + 1 /* BusFault */
  .word probe_fault + 1 /* UsageFault */
  .rept 9
  .word probe_fault + 1
  .endr

.section .text.start, "ax", %progbits
.align 2
.global probe_start
.type probe_start, %function
.thumb_func
probe_start:
  cpsid i
  ldr r0, =MAILBOX
  ldr r1, =MAGIC
  str r1, [r0, #0]

  /* Route faults to the local diagnostic handler before any protected read. */
  ldr r1, =probe_vectors
  ldr r2, =SCB_VTOR
  str r1, [r2]
  dsb sy
  isb sy

  movs r1, #1
  str r1, [r0, #4]        /* state: alive */
  movs r1, #0
  str r1, [r0, #8]        /* command */
  str r1, [r0, #0x14]     /* result word count */
  dsb sy

probe_loop:
  ldr r1, [r0, #8]
  cmp r1, #0
  beq probe_loop
  cmp r1, #1
  beq probe_two_words
  cmp r1, #2
  beq copy_flash_chunk
  movs r2, #0xe1
  str r2, [r0, #4]
  b command_done

probe_two_words:
  movs r1, #0x10
  str r1, [r0, #4]        /* state: about to touch internal flash */
  dsb sy
  ldr r2, =FLASH_BASE
  ldr r3, [r2, #0]
  str r3, [r0, #0x18]
  ldr r3, [r2, #4]
  str r3, [r0, #0x1c]
  movs r1, #2
  str r1, [r0, #0x14]
  movs r1, #0x11
  str r1, [r0, #4]        /* state: protected read completed */
  b command_done

copy_flash_chunk:
  movs r1, #0x20
  str r1, [r0, #4]
  ldr r2, [r0, #0x0c]     /* source address */
  ldr r5, [r0, #0x10]     /* 32-bit word count */
  ldr r3, =FLASH_BASE
  cmp r2, r3
  blo bounds_error
  cmp r5, #1
  blo bounds_error
  cmp r5, #256
  bhi bounds_error
  lsls r4, r5, #2
  adds r4, r2, r4
  ldr r3, =FLASH_END
  cmp r4, r3
  bhi bounds_error
  ldr r6, =BUFFER

copy_loop:
  ldr r7, [r2], #4
  str r7, [r6], #4
  subs r5, r5, #1
  bne copy_loop
  ldr r5, [r0, #0x10]
  str r5, [r0, #0x14]
  movs r1, #0x21
  str r1, [r0, #4]        /* state: chunk ready */
  b command_done

bounds_error:
  movs r1, #0xe2
  str r1, [r0, #4]

command_done:
  movs r1, #0
  str r1, [r0, #8]
  dsb sy
  b probe_loop

.size probe_start, . - probe_start

.align 2
.global probe_fault
.type probe_fault, %function
.thumb_func
probe_fault:
  cpsid i
  ldr r0, =MAILBOX
  ldr r1, =MAGIC
  str r1, [r0, #0]
  movs r1, #0xf0
  str r1, [r0, #4]
  ldr r2, =SCB_CFSR
  ldr r3, [r2]
  str r3, [r0, #0x20]
  ldr r2, =SCB_HFSR
  ldr r3, [r2]
  str r3, [r0, #0x24]
  ldr r2, =SCB_MMFAR
  ldr r3, [r2]
  str r3, [r0, #0x28]
  ldr r2, =SCB_BFAR
  ldr r3, [r2]
  str r3, [r0, #0x2c]
  dsb sy
fault_loop:
  b fault_loop

.size probe_fault, . - probe_fault
