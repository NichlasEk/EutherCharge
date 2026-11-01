.syntax unified
.cpu cortex-m4
.thumb

.section .text, "ax", %progbits
.global payload_entry
.type payload_entry, %function
.thumb_func
payload_entry:
    ldr r0, mailbox_address
    ldr r1, mailbox_magic
    str r1, [r0, #0]
    ldr r1, mailbox_tag
    str r1, [r0, #4]
    ldr r1, mailbox_state
    str r1, [r0, #8]
1:
    b 1b

.align 2
mailbox_address:
    .word 0x20001700
mailbox_magic:
    .word 0x4b574345
mailbox_tag:
    .word 0x5352414d
mailbox_state:
    .word 0x00000042
.size payload_entry, . - payload_entry
