# KW520 embedded-NUL copy diagnostic

This fixed parser probe does not choose a new control-flow target. It preserves
the recurrent word `0x080093f3` at copied payload offsets 252--255 while placing
an earlier NUL at offset 100 and a unique marker after it. Allocation remains
320, for which physical captures showed a 256-byte copy frontier.

The paired SRAM capture distinguishes:

- fixed-size copy: the post-NUL marker is present;
- stop-at-NUL copy: prior SRAM remains after offset 100;
- fixed-width NUL padding: the remaining copy window is zero-filled.

Install the inactive data sector first. Activate the already qualified title
pointer only after a normal cold start. Recovery order is pointer first, cold
start, then data sector to all-FF, followed by another cold start.
