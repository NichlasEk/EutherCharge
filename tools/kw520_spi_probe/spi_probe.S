.syntax unified
.cpu cortex-m4
.thumb

.equ MAILBOX,      0x20001700
.equ READ_BUFFER,  0x20001800
.equ STACK_TOP,    0x20003f00
.equ GPIOA,        0x48000000
.equ GPIOB,        0x48000400
.equ SPI2,         0x40003800
.equ WDT,          0x40003000
.equ SCB_VTOR,     0xe000ed08
.equ SCB_CFSR,     0xe000ed28
.equ SCB_HFSR,     0xe000ed2c
.equ MAGIC,        0x4b575350  /* "KWSP" */
.equ PA8,          0x00000100

.section .vectors, "a", %progbits
.align 7
.global probe_vectors
probe_vectors:
  .word STACK_TOP
  .word probe_start + 1
  .word probe_fault + 1
  .word probe_fault + 1
  .word probe_fault + 1
  .word probe_fault + 1
  .word probe_fault + 1
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
  ldr r6, =MAILBOX
  ldr r1, =MAGIC
  str r1, [r6, #0]
  ldr r1, =probe_vectors
  ldr r2, =SCB_VTOR
  str r1, [r2]
  dsb sy
  isb sy

  ldr r4, =GPIOA
  ldr r7, =GPIOB
  ldr r5, =SPI2
  ldr r1, [r4, #0x00]
  str r1, [r6, #0x40]     /* GPIOA CFGR */
  ldr r2, [r4, #0x14]
  str r2, [r6, #0x44]     /* GPIOA ODT */
  ldr r2, [r7, #0x00]
  str r2, [r6, #0x48]     /* GPIOB CFGR */
  ldr r2, [r7, #0x0c]
  str r2, [r6, #0x4c]     /* GPIOB PULL */
  ldr r2, [r7, #0x24]
  str r2, [r6, #0x50]     /* GPIOB MUXH */
  ldr r2, [r5, #0x00]
  str r2, [r6, #0x54]     /* SPI2 CTRL1 */
  ldr r3, [r5, #0x04]
  str r3, [r6, #0x58]     /* SPI2 CTRL2 */
  ldr r3, [r5, #0x08]
  str r3, [r6, #0x5c]     /* SPI2 STS */

  /* Require physically traced PA8 CS and the observed SPI2 pin roles. */
  ldr r1, [r4, #0x00]
  lsrs r2, r1, #16
  ands r2, r2, #3
  cmp r2, #1              /* PA8 GPIO output */
  bne precondition_error
  ldr r2, [r4, #0x14]
  tst r2, #PA8            /* flash CS must start high */
  beq precondition_error
  ldr r1, [r7, #0x00]
  lsrs r2, r1, #26
  ands r2, r2, #3
  cmp r2, #2              /* PB13 AF */
  bne precondition_error
  lsrs r2, r1, #28
  ands r2, r2, #3
  cmp r2, #2              /* PB14 AF */
  bne precondition_error
  lsrs r2, r1, #30
  ands r2, r2, #3
  cmp r2, #2              /* PB15 AF */
  bne precondition_error
  ldr r2, [r5, #0x00]
  uxth r2, r2
  ldr r3, =0x0357         /* enabled master, mode 3, /8, software CS */
  cmp r2, r3
  bne precondition_error
  ldr r2, [r5, #0x08]
  tst r2, #2              /* transmit buffer empty */
  beq precondition_error

  movs r1, #1
  str r1, [r6, #4]
  /* Preserve only the fixed one-shot command 3: offset 0, length 16. */
  ldr r1, [r6, #8]
  cmp r1, #4
  beq initial_command_ready
  cmp r1, #3
  bne clear_initial_command
  ldr r2, [r6, #0x0c]
  cmp r2, #0
  bne clear_initial_command
  ldr r2, [r6, #0x10]
  cmp r2, #16
  beq initial_command_ready
clear_initial_command:
  movs r1, #0
  str r1, [r6, #8]
initial_command_ready:
  dsb sy

command_loop:
  ldr r1, [r6, #8]
  cmp r1, #0
  beq command_loop
  cmp r1, #1
  beq jedec_probe
  cmp r1, #2
  beq read_data
  cmp r1, #3
  beq jedec_probe
  cmp r1, #4
  beq jedec_probe
  movs r1, #0xe0
  str r1, [r6, #4]
  b command_done

precondition_error:
  movs r1, #0xe1
  str r1, [r6, #4]
  movs r1, #0
  str r1, [r6, #8]
precondition_stop:
  b precondition_stop

jedec_probe:
  movs r1, #0x10
  str r1, [r6, #4]
  ldr r1, [r5, #0x08]
  str r1, [r6, #0x24]
  tst r1, #1
  beq receive_empty
  ldr r1, [r5, #0x0c]     /* drain one stale received byte */
receive_empty:
  ldr r1, =PA8
  str r1, [r4, #0x28]     /* PA8 low: flash CS asserted */
  dsb sy

  movs r0, #0x9f
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  movs r0, #0xff
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  str r0, [r6, #0x18]
  movs r0, #0xff
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  str r0, [r6, #0x1c]
  movs r0, #0xff
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  str r0, [r6, #0x20]

  ldr r2, =0x00040000
wait_not_busy:
  ldr r1, [r5, #0x08]
  tst r1, #0x80
  beq transfer_done
  subs r2, r2, #1
  bne wait_not_busy
  b spi_timeout

transfer_done:
  ldr r2, =PA8
  str r2, [r4, #0x18]     /* PA8 high: CS released */
  dsb sy
  ldr r1, [r5, #0x08]
  str r1, [r6, #0x28]
  ldr r1, [r4, #0x14]
  str r1, [r6, #0x2c]
  ldr r1, [r6, #0x18]
  cmp r1, #0x1c
  bne jedec_mismatch
  ldr r1, [r6, #0x1c]
  cmp r1, #0x30
  bne jedec_mismatch
  ldr r1, [r6, #0x20]
  cmp r1, #0x16
  bne jedec_mismatch
  ldr r1, [r6, #8]
  cmp r1, #3
  beq read_data            /* fixed one-shot JEDEC -> offset 0 + 16 */
  cmp r1, #4
  beq crc_full_flash       /* fixed one-shot JEDEC -> 4 MiB CRC-32B */
  movs r1, #0x11
  str r1, [r6, #4]
  b command_done

jedec_mismatch:
  movs r1, #0x12
  str r1, [r6, #4]
  b command_done

crc_full_flash:
  /* Fixed, read-only fingerprint of the complete 4 MiB EN25Q32. */
  movs r1, #0x40
  str r1, [r6, #4]
  movs r1, #0
  str r1, [r6, #0x14]
  str r1, [r6, #0x34]
  str r1, [r6, #0x38]
  ldr r7, =WDT
  ldr r1, =0x0000aaaa
  str r1, [r7]             /* refresh only; no unlock/configuration change */
  ldr r1, [r5, #0x08]
  tst r1, #1
  beq crc_receive_empty
  ldr r1, [r5, #0x0c]
crc_receive_empty:
  ldr r1, =PA8
  str r1, [r4, #0x28]
  dsb sy

  movs r0, #0x03
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  movs r0, #0
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  movs r0, #0
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  movs r0, #0
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout

  ldr r8, =0xffffffff      /* reflected CRC-32 initial value */
  ldr r9, =0x00400000
  movs r10, #0
  ldr r12, =0xedb88320     /* reflected IEEE polynomial */
crc_byte_loop:
  movs r0, #0xff
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  eors r8, r8, r0
  movs r11, #8
crc_bit_loop:
  lsrs r8, r8, #1
  bcc crc_no_xor
  eors r8, r8, r12
crc_no_xor:
  subs r11, r11, #1
  bne crc_bit_loop
  adds r10, r10, #1
  lsls r1, r10, #20       /* publish progress every 4096 bytes */
  bne crc_no_progress
  str r10, [r6, #0x14]
  lsrs r1, r10, #12
  str r1, [r6, #0x38]
  ldr r1, =0x0000aaaa
  str r1, [r7]             /* keep original active WDT alive on progress */
crc_no_progress:
  cmp r10, r9
  blo crc_byte_loop

  ldr r2, =0x00040000
crc_wait_not_busy:
  ldr r1, [r5, #0x08]
  tst r1, #0x80
  beq crc_transfer_done
  subs r2, r2, #1
  bne crc_wait_not_busy
  b spi_timeout

crc_transfer_done:
  ldr r2, =PA8
  str r2, [r4, #0x18]
  dsb sy
  mvns r8, r8             /* standard CRC-32B final xor */
  str r8, [r6, #0x34]
  str r10, [r6, #0x14]
  movs r1, #0x41
  str r1, [r6, #4]
  b command_done

read_data:
  /*
   * Command 2 is deliberately read-only and bounded:
   *   mailbox +0x0c = 24-bit EN25Q32 source address
   *   mailbox +0x10 = byte count, 1..8192
   *   mailbox +0x14 = completed byte count
   *   data appears at READ_BUFFER
   */
  movs r1, #0
  str r1, [r6, #0x14]
  ldr r8, [r6, #0x0c]
  ldr r9, [r6, #0x10]
  cmp r9, #0
  beq read_bounds_error
  ldr r1, =0x00002000
  cmp r9, r1
  bhi read_bounds_error
  ldr r1, =0x003fffff
  cmp r8, r1
  bhi read_bounds_error
  adds r2, r8, r9
  bcs read_bounds_error
  ldr r1, =0x00400000
  cmp r2, r1
  bhi read_bounds_error

  movs r1, #0x20
  str r1, [r6, #4]
  ldr r1, [r5, #0x08]
  tst r1, #1
  beq read_receive_empty
  ldr r1, [r5, #0x0c]     /* drain one stale received byte */
read_receive_empty:
  ldr r1, =PA8
  str r1, [r4, #0x28]     /* PA8 low: flash CS asserted */
  dsb sy

  movs r0, #0x03          /* EN25Q32 Read Data */
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  lsrs r0, r8, #16
  uxtb r0, r0
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  lsrs r0, r8, #8
  uxtb r0, r0
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  uxtb r0, r8
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout

  ldr r7, =READ_BUFFER
  movs r10, #0
read_byte_loop:
  movs r0, #0xff
  bl spi_xfer
  cmp r1, #0
  bne spi_timeout
  strb r0, [r7, r10]
  adds r10, r10, #1
  str r10, [r6, #0x14]
  cmp r10, r9
  blo read_byte_loop

  ldr r2, =0x00040000
read_wait_not_busy:
  ldr r1, [r5, #0x08]
  tst r1, #0x80
  beq read_transfer_done
  subs r2, r2, #1
  bne read_wait_not_busy
  b spi_timeout

read_transfer_done:
  ldr r2, =PA8
  str r2, [r4, #0x18]     /* PA8 high: CS released */
  dsb sy
  movs r1, #0x21
  str r1, [r6, #4]
  b command_done

read_bounds_error:
  movs r1, #0xe3
  str r1, [r6, #4]
  b command_done

spi_timeout:
  ldr r2, =PA8
  str r2, [r4, #0x18]     /* always release candidate CS */
  movs r1, #0xe2
  str r1, [r6, #4]

command_done:
  movs r1, #0
  str r1, [r6, #8]
  dsb sy
  b command_loop

.size probe_start, . - probe_start

.align 2
.type spi_xfer, %function
.thumb_func
spi_xfer:
  ldr r2, =SPI2
  ldr r3, =0x00040000
wait_tx_empty:
  ldr r1, [r2, #0x08]
  tst r1, #2
  bne transmit_byte
  subs r3, r3, #1
  bne wait_tx_empty
  movs r1, #1
  bx lr
transmit_byte:
  str r0, [r2, #0x0c]
  ldr r3, =0x00040000
wait_rx_full:
  ldr r1, [r2, #0x08]
  tst r1, #1
  bne receive_byte
  subs r3, r3, #1
  bne wait_rx_full
  movs r1, #1
  bx lr
receive_byte:
  ldr r0, [r2, #0x0c]
  uxtb r0, r0
  movs r1, #0
  bx lr
.size spi_xfer, . - spi_xfer

.align 2
.global probe_fault
.type probe_fault, %function
.thumb_func
probe_fault:
  cpsid i
  ldr r0, =GPIOA
  ldr r1, =PA8
  str r1, [r0, #0x18]
  ldr r0, =MAILBOX
  ldr r1, =MAGIC
  str r1, [r0, #0]
  movs r1, #0xf0
  str r1, [r0, #4]
  ldr r2, =SCB_CFSR
  ldr r3, [r2]
  str r3, [r0, #0x70]
  ldr r2, =SCB_HFSR
  ldr r3, [r2]
  str r3, [r0, #0x74]
  dsb sy
fault_loop:
  b fault_loop
.size probe_fault, . - probe_fault
