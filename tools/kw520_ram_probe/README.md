# KW520 SRAM probe

This is a deliberately bounded Cortex-M4 helper for the protected
AT32F421C8T7. It is linked for the verified zero-filled SRAM window beginning at
`0x20001000` and has no internal- or external-flash write routine.

Mailbox at `0x20001700`:

| Offset | Meaning |
|---:|---|
| `+0x00` | magic `0x4b575250` (`KWRP`) |
| `+0x04` | state |
| `+0x08` | command: 1 probe two words, 2 copy chunk |
| `+0x0c` | chunk source, limited to internal flash |
| `+0x10` | chunk word count, 1–256 |
| `+0x14` | completed word count |
| `+0x18` | first probe word |
| `+0x1c` | second probe word |
| `+0x20..0x2c` | CFSR/HFSR/MMFAR/BFAR captured by local fault handler |

States: `1` alive, `0x10` before protected read, `0x11` two-word read done,
`0x20` chunk starting, `0x21` chunk ready, `0xe1` bad command, `0xe2` invalid
range, and `0xf0` fault caught.

The chunk buffer is `0x20001800` and holds at most 1 KiB. Source addresses are
hard-limited to `0x08000000–0x0800ffff`. A host can therefore request 64 chunks
if protected-state execution and internal-flash reads both prove possible.

Build reproducibly with:

```sh
make -C tools/kw520_ram_probe
```

The current 308-byte binary has SHA-256
`abc47fdb82ec7dd17fdf6e11166e1973341cb092382d2c60d6a2149a460f5663`.
After a qualified 64-chunk acquisition, `assemble_dump.py` refuses missing or
wrong-sized chunks, an implausible Cortex-M vector table, a changed helper, or
an incomplete SRAM restoration. It can also require byte equality with an
independent readout before it writes the combined image.

Passing the existing MEM-AP SRAM write/restore test does not prove this code can
execute. The first live gate must only load the helper, redirect a halted core,
and check for state `1`. Command 1 is a separate gate. Preserve and restore the
overwritten SRAM window during every experiment.

Live gates on 2026-10-31 proved exact helper load/readback and SRAM execution.
Command 1 completed without a fault but returned two zero words for
`0x08000000`, not a plausible vector table. This matches AT32F421 low-level FAP:
main Flash reads are forbidden in debug mode or when executing from SRAM. The
prepared full-dump configuration is therefore hard-stopped and must not be
enabled merely to produce a 64 KiB zero image.
