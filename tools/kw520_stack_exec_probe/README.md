# KW520 normally booted SRAM-marker gate

This gate tests one fixed control-flow hypothesis. A 32-byte Thumb stub is
placed at the start of the external title payload. The verified 256-byte parser
copy places it at `0x20003978`, while payload offsets 252--255 contain the Thumb
address `0x20003979`. The stub can only write twelve fixed bytes to SRAM
mailbox `0x20001700` and loop. It contains no internal-flash read, peripheral
access or external-flash write.

Install the inactive data sector first. Activate the title pointer only after a
normal cold start. Recovery order is pointer first, cold start, then data sector
to all-FF, followed by another cold start.

## Physical result

The copied stub, all 256 copied bytes and selected word `0x20003979` matched in
SRAM. The mailbox remained all zero after boot and after one working navigation
button event. This gate therefore does **not** prove code execution. The stable
word at payload offset 252 is not used as control flow by the tested paths.
Both external sectors were restored exactly; do not repeat this candidate with
other arbitrary addresses.
