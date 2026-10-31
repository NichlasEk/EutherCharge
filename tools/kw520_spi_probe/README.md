# KW520 read-only SPI2 probe

This SRAM helper is a deliberately bounded transport qualification step. It
uses the already-observed runtime configuration only if physically traced PA8
is a high GPIO output, PB13/PB14/PB15 are AF0, and SPI2 is exactly enabled as
master/mode 3, prescaler 8, software CS. It then waits for host command 1,
pulses only PA8, and initially transmits `9F FF FF FF`. It recognizes only
EN25Q32 JEDEC `1C 30 16`.

After that identity gate, host command 2 may use only the EN25Q32 `03` Read
Data operation. The source address is restricted to the 4 MiB device and each
request to 1--8192 bytes. Data is returned in SRAM at `0x20001800`; the helper
never interprets it and never issues a mutating flash instruction.

For the first physical data gate, command 3 is an even narrower one-shot mode.
It is accepted at startup only when the preloaded source is exactly zero and
the length exactly 16. A single core run then performs JEDEC identification,
requires `1C 30 16`, reads those 16 bytes with fixed opcode `03`, and stops in
the command loop. This avoids a second resume of the protected MCU.

Command 4 is a fixed whole-device fingerprint. After the same JEDEC gate it
issues `03 00 00 00`, reads exactly 4 MiB continuously, and calculates standard
reflected CRC-32B (`EDB88320`, initial/final XOR `FFFFFFFF`) in core registers.
Only progress and the final 32-bit CRC enter the mailbox. It adds no flash-write
opcode and transfers no bulk flash contents through the debug link.

The installed hardware watchdog was proven by `CRM_CTRLSTS.WDTRSTF` after two
repeatable resets. During command 4 only, the helper writes the vendor-defined
reload key `AAAA` to `WDT_CMD` once at entry and after each 4096 bytes of genuine
SPI progress. It never unlocks or changes the divider/reload configuration. If
progress stops, refreshing stops and the watchdog still resets the target.

There is no write-enable (`06`), erase, page-program, status-register-write,
internal-flash operation, or generic host-selected SPI opcode in the binary.
Every timeout and the fault handler release PA8 high. A matching ID proves
PA8/SPI2 routing; a mismatch stops the experiment rather than trying alternate
GPIOs.

The first live attempt deliberately split load and execution into two OpenOCD
sessions. The helper returned state `0xe1` because GPIOB and SPI2 had reverted
to reset values before the second session; it never toggled PB11 or sent `0x9f`.
SRAM restored exactly. The next configuration keeps live-register validation,
load, execution, JEDEC read, and restoration inside one uninterrupted session.

## Qualified hardware result (2026-10-31)

The corrected-wiring run qualified the complete read-only path on the physical
KW520: J-Link/MEM-AP -> SRAM helper -> PA8 chip select and SPI2 -> EN25Q32.
The flash returned JEDEC ID `1c 30 16`. A fixed 16-byte read at offset zero
matched the installed EutherCharge image, and command 4 processed exactly
4,194,304 bytes with CRC-32B `268f3bd7`. That CRC matches the independently
read installed image whose SHA-256 is
`4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329`.

The qualified helper is 996 bytes with SHA-256
`5b55a03cdd89444487622d5ab4338882a406f844ffe06135b70765e64286aa71`.
Its target readback was exact. The code, mailbox, buffer and stack SRAM windows
were restored bit-for-bit, VTOR was restored to `0x08000000`, and final DP
CTRL/STAT was `0x00000040`. The watchdog was refreshed exactly 1,024 times,
once per 4,096 bytes of real progress, without changing its divider or reload.

This qualifies external-flash transport only. AT32F421 main flash remains
protected by FAP: the separate SRAM internal-flash probe returned zero words,
not firmware. Any future attempt to disclose internal firmware through the
external SPI path therefore needs a new, independently demonstrated primitive
in the original firmware; this result must not be described as an MCU firmware
dump.
