.syntax unified
.cpu cortex-m4
.thumb

.equ CODE_BASE,       0x20001000
.equ MAILBOX,         0x20001700
.equ SOURCE,          0x20001800
.equ DESTINATION,     0x20001900
.equ CALL_STACK_BASE, 0x20002200
.equ CALL_STACK_TOP,  0x20002300

.equ SCB_VTOR,        0xe000ed08
.equ SCB_CFSR,        0xe000ed28
.equ SCB_HFSR,        0xe000ed2c
.equ SCB_MMFAR,       0xe000ed34
.equ SCB_BFAR,        0xe000ed38
.equ DHCSR,           0xe000edf0
.equ MPU_TYPE,        0xe000ed90
.equ MPU_CTRL,        0xe000ed94
.equ MPU_RNR,         0xe000ed98
.equ MPU_RBAR,        0xe000ed9c
.equ MPU_RASR,        0xe000eda0

.equ MAGIC,           0x4b57434f  /* KWCO */
.equ ARM_MAGIC,       0x43414c4c  /* CALL */
.equ CANDIDATE_COUNT, 19

/* Mailbox offsets. */
.equ MB_MAGIC,        0x00
.equ MB_STATE,        0x04
.equ MB_ARM,          0x08
.equ MB_COMMAND,      0x0c
.equ MB_INDEX,        0x10
.equ MB_CANDIDATE,    0x14
.equ MB_MPU_TYPE,     0x18
.equ MB_MPU_BEFORE,   0x1c
.equ MB_RESULT_R0,    0x20
.equ MB_MATCHED,      0x24
.equ MB_CFSR,         0x28
.equ MB_HFSR,         0x2c
.equ MB_MMFAR,        0x30
.equ MB_BFAR,         0x34
.equ MB_STACKED_PC,   0x38
.equ MB_STACKED_LR,   0x3c
.equ MB_GUARD_BEFORE, 0x40
.equ MB_GUARD_AFTER,  0x44
.equ MB_FAULT_PHASE,  0x48
.equ MB_COUNT,        0x4c

/* MPU RASR values: no privileged background map is enabled. */
.equ MPU_FLASH_64K_RO_X,  0x0602001f
.equ MPU_CODE_1K_RO_X,   0x06020013
.equ MPU_DATA_256_RW_XN, 0x1306000f
.equ MPU_DATA_256_RO_XN, 0x1602000f

.section .vectors, "a", %progbits
.align 7
.global oracle_vectors
oracle_vectors:
  .word CALL_STACK_TOP
  .word oracle_start + 1
  .rept 14
  .word oracle_fault + 1
  .endr

.section .text.start, "ax", %progbits
.align 2
.global oracle_start
.type oracle_start, %function
.thumb_func
oracle_start:
  cpsid i
  ldr r0, =MAILBOX
  ldr r1, =MAGIC
  str r1, [r0, #MB_MAGIC]

  ldr r1, =oracle_vectors
  ldr r2, =SCB_VTOR
  str r1, [r2]
  dsb sy
  isb sy

  ldr r1, =MPU_TYPE
  ldr r2, [r1]
  str r2, [r0, #MB_MPU_TYPE]
  ldr r1, =MPU_CTRL
  ldr r2, [r1]
  str r2, [r0, #MB_MPU_BEFORE]
  ldr r1, =CANDIDATE_COUNT
  str r1, [r0, #MB_COUNT]

  movs r1, #0
  str r1, [r0, #MB_COMMAND]
  str r1, [r0, #MB_CANDIDATE]
  str r1, [r0, #MB_RESULT_R0]
  str r1, [r0, #MB_MATCHED]
  str r1, [r0, #MB_CFSR]
  str r1, [r0, #MB_HFSR]
  str r1, [r0, #MB_MMFAR]
  str r1, [r0, #MB_BFAR]
  str r1, [r0, #MB_STACKED_PC]
  str r1, [r0, #MB_STACKED_LR]
  str r1, [r0, #MB_FAULT_PHASE]
  movs r1, #1
  str r1, [r0, #MB_STATE]
  dsb sy

oracle_loop:
  ldr r1, [r0, #MB_COMMAND]
  cmp r1, #0
  beq oracle_loop
  cmp r1, #1
  beq inventory_done
  cmp r1, #2
  beq prepare_call
  cmp r1, #3
  beq prepare_detach
  movs r1, #0xe1
  str r1, [r0, #MB_STATE]
  b command_done

inventory_done:
  movs r1, #0x10
  str r1, [r0, #MB_STATE]
  b command_done

prepare_call:
  movs r5, #0
  b prepare_common

prepare_detach:
  movs r5, #1

prepare_common:
  ldr r1, [r0, #MB_ARM]
  ldr r2, =ARM_MAGIC
  cmp r1, r2
  bne bad_arm
  ldr r1, [r0, #MB_MPU_TYPE]
  ubfx r1, r1, #8, #8
  cmp r1, #6
  blo bad_mpu
  ldr r1, [r0, #MB_INDEX]
  cmp r1, #CANDIDATE_COUNT
  bhs bad_index
  ldr r2, =candidate_table
  ldr r4, [r2, r1, lsl #2]
  str r4, [r0, #MB_CANDIDATE]

  /* Fixed source, destination, and two guards are initialized before MPU. */
  ldr r1, =SOURCE
  ldr r2, =0x11223344
  movs r3, #16
source_fill:
  str r2, [r1], #4
  add r2, r2, #0x01010101
  subs r3, r3, #1
  bne source_fill

  ldr r1, =DESTINATION
  ldr r2, =0xa5a5a5a5
  movs r3, #16
destination_fill:
  str r2, [r1], #4
  subs r3, r3, #1
  bne destination_fill
  ldr r1, =SOURCE + 0xfc
  ldr r2, =0xdeadbeef
  str r2, [r1]
  ldr r1, =DESTINATION + 0x40
  ldr r2, =0xbaadf00d
  str r2, [r1]

  cmp r5, #0
  bne wait_for_debug_detach
  movs r1, #0x20
  str r1, [r0, #MB_STATE]
  b configure_for_call

wait_for_debug_detach:
  movs r1, #0x40
  str r1, [r0, #MB_STATE]
  dsb sy
  ldr r1, =DHCSR
detach_poll:
  ldr r2, [r1]
  tst r2, #1
  bne detach_poll
  movs r1, #0x41
  str r1, [r0, #MB_STATE]
  dsb sy
  /* Give the host enough time to clear CDBGPWRUPREQ after C_DEBUGEN falls. */
  ldr r3, =2000000
detach_guard_delay:
  subs r3, r3, #1
  bne detach_guard_delay

configure_for_call:
  bl configure_mpu

  /* Candidate runs unprivileged on PSP. Unknown peripheral/system accesses
     therefore fault; no MPU background map exists. */
  ldr r1, =CALL_STACK_TOP
  msr psp, r1
  movs r1, #3
  msr control, r1
  isb sy

  ldr r0, =MAILBOX
  movs r1, #0x21
  str r1, [r0, #MB_STATE]
  ldr r0, =DESTINATION
  ldr r1, =SOURCE
  movs r2, #32
  movs r3, #0
  blx r4

candidate_returned:
  ldr r1, =MAILBOX
  str r0, [r1, #MB_RESULT_R0]
  movs r0, #0x30
  str r0, [r1, #MB_STATE]
  dsb sy
  udf #0

bad_arm:
  movs r1, #0xe2
  str r1, [r0, #MB_STATE]
  b command_done
bad_mpu:
  movs r1, #0xe3
  str r1, [r0, #MB_STATE]
  b command_done
bad_index:
  movs r1, #0xe4
  str r1, [r0, #MB_STATE]

command_done:
  movs r1, #0
  str r1, [r0, #MB_COMMAND]
  dsb sy
  b oracle_loop

.size oracle_start, . - oracle_start

.align 2
.type configure_mpu, %function
.thumb_func
configure_mpu:
  push {lr}
  ldr r0, =MPU_CTRL
  movs r1, #0
  str r1, [r0]
  dsb sy
  isb sy

  /* Region 0: protected main flash, read-only and executable. */
  movs r0, #0
  ldr r1, =0x08000000
  ldr r2, =MPU_FLASH_64K_RO_X
  bl set_region
  /* Region 1: this oracle's 1 KiB code/vector block. */
  movs r0, #1
  ldr r1, =CODE_BASE
  ldr r2, =MPU_CODE_1K_RO_X
  bl set_region
  /* Region 2: mailbox, unprivileged read/write, never execute. */
  movs r0, #2
  ldr r1, =MAILBOX
  ldr r2, =MPU_DATA_256_RW_XN
  bl set_region
  /* Region 3: immutable source block. */
  movs r0, #3
  ldr r1, =SOURCE
  ldr r2, =MPU_DATA_256_RO_XN
  bl set_region
  /* Region 4: destination/canary block. */
  movs r0, #4
  ldr r1, =DESTINATION
  ldr r2, =MPU_DATA_256_RW_XN
  bl set_region
  /* Region 5: dedicated PSP/MSP block. */
  movs r0, #5
  ldr r1, =CALL_STACK_BASE
  ldr r2, =MPU_DATA_256_RW_XN
  bl set_region

  ldr r0, =MPU_CTRL
  movs r1, #1            /* ENABLE, no PRIVDEFENA, no HFNMIENA */
  str r1, [r0]
  dsb sy
  isb sy
  pop {pc}
.size configure_mpu, . - configure_mpu

.align 2
.type set_region, %function
.thumb_func
set_region:
  ldr r3, =MPU_RNR
  str r0, [r3]
  ldr r3, =MPU_RBAR
  str r1, [r3]
  ldr r3, =MPU_RASR
  str r2, [r3]
  bx lr
.size set_region, . - set_region

.align 2
.global oracle_fault
.type oracle_fault, %function
.thumb_func
oracle_fault:
  cpsid i
  mov r7, lr

  /* MPU is automatically inactive in HardFault because HFNMIENA is clear;
     disable it explicitly before inspecting the result. */
  ldr r0, =MPU_CTRL
  movs r1, #0
  str r1, [r0]
  dsb sy
  isb sy

  ldr r0, =MAILBOX
  ldr r1, [r0, #MB_STATE]
  str r1, [r0, #MB_FAULT_PHASE]

  tst r7, #4
  ite eq
  mrseq r6, msp
  mrsne r6, psp
  ldr r2, [r6, #0x14]
  str r2, [r0, #MB_STACKED_LR]
  ldr r2, [r6, #0x18]
  str r2, [r0, #MB_STACKED_PC]

  ldr r1, =SCB_CFSR
  ldr r2, [r1]
  str r2, [r0, #MB_CFSR]
  ldr r1, =SCB_HFSR
  ldr r2, [r1]
  str r2, [r0, #MB_HFSR]
  ldr r1, =SCB_MMFAR
  ldr r2, [r1]
  str r2, [r0, #MB_MMFAR]
  ldr r1, =SCB_BFAR
  ldr r2, [r1]
  str r2, [r0, #MB_BFAR]

  ldr r1, =SOURCE + 0xfc
  ldr r2, [r1]
  str r2, [r0, #MB_GUARD_BEFORE]
  ldr r1, =DESTINATION + 0x40
  ldr r2, [r1]
  str r2, [r0, #MB_GUARD_AFTER]

  ldr r1, [r0, #MB_FAULT_PHASE]
  cmp r1, #0x30
  bne candidate_faulted

  ldr r1, =SOURCE
  ldr r2, =DESTINATION
  movs r3, #0
verify_copy:
  ldr r4, [r1, r3]
  ldr r5, [r2, r3]
  cmp r4, r5
  bne copy_mismatch
  adds r3, r3, #4
  cmp r3, #32
  blo verify_copy
  movs r6, #32
  ldr r5, =0xa5a5a5a5
verify_tail:
  ldr r4, [r2, r6]
  cmp r4, r5
  bne copy_mismatch
  adds r6, r6, #4
  cmp r6, #64
  blo verify_tail
  str r3, [r0, #MB_MATCHED]
  ldr r4, [r0, #MB_GUARD_BEFORE]
  ldr r5, =0xdeadbeef
  cmp r4, r5
  bne copy_mismatch
  ldr r4, [r0, #MB_GUARD_AFTER]
  ldr r5, =0xbaadf00d
  cmp r4, r5
  bne copy_mismatch
  movs r1, #0x31
  str r1, [r0, #MB_STATE]
  b fault_stop

copy_mismatch:
  str r3, [r0, #MB_MATCHED]
  movs r1, #0x32
  str r1, [r0, #MB_STATE]
  b fault_stop

candidate_faulted:
  movs r1, #0xf0
  str r1, [r0, #MB_STATE]

fault_stop:
  movs r1, #0
  msr control, r1
  dsb sy
  isb sy
fault_loop:
  b fault_loop
.size oracle_fault, . - oracle_fault

.align 2
candidate_table:
  .word 0x08000b71
  .word 0x08001325
  .word 0x08001371
  .word 0x080015eb
  .word 0x08002433
  .word 0x0800742f
  .word 0x0800750b
  .word 0x0800752d
  .word 0x08007af1
  .word 0x08007b0d
  .word 0x080093f3
  .word 0x0800942d
  .word 0x08009a73
  .word 0x08009e91
  .word 0x0800a04d
  .word 0x0800a0af
  .word 0x0800a0b3
  .word 0x0800a9dd
  .word 0x0800ad8f
