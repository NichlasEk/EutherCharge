# KW520: external flash as input to original firmware

## Objective and boundary

The user clarified the goal: analyze the existing SPI dump as a route to make the original MCU firmware disclose its protected internal flash. Reading/programming SPI through J-Link is only a possible transport prerequisite, not the goal. No target traffic or modified image was applied during this analysis.

## Evidence from the actual dump

Reference SHA-256 d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2 was rechecked. All eight banks parse: 162 entries each, 1296 total. Entries have relative big-endian32 SPI offsets and big-endian16 lengths including the terminating NUL. Original allocations range3..113 bytes; every parsed string terminates at the declared allocation, with no earlier NUL. None contains a percent byte. This does not establish whether a format-string sink exists in the MCU program.

Only these 4KiB-sector ranges differ from erased FF: [0,c000), [380000,382000), [383000,384000). Prior vector scan found no ordinary aligned Cortex-M image candidate. This does not exclude compressed code or other formats. A recognizable128x32 mono logo exists, but changing it did not visibly change the observed boot flow. Language changes were physically accepted previously, making language parsing the stronger known input surface.

Audit output: build/kw520-jlink-20261031/spi-parser-surface-audit.json. The PC parser's validation is not evidence of bounds checking in the MCU firmware.

## Concrete hypotheses to distinguish

1. Length-based copying into a fixed RAM buffer. The16-bit resource length is controlled by SPI contents; actual firmware limits and destination buffer size are unknown. A crash alone would not demonstrate readout or controlled execution.
2. Incorrect pointer/offset arithmetic or resource-kind selection. Current pointers are external-flash offsets, not verified CPU addresses. Substituting08000000 does not automatically address internal flash; the SPI driver may truncate or wrap the address.
3. Text renderer treating stored text as a printf-style format. No original strings contain percent signs, so this remains unproven. A bounded literal-vs-format diagnostic would precede any exploitation; no such test was written or run here.
4. Persistent metadata/history interpreted as counts, lengths, or commands. Their semantics and safety impact are unresolved, so they are a lower-priority surface than known menu strings.
5. External staged-update marker or command interpreter. No such mechanism is evidenced in this dump. The RT890 updater example is a different product and does not demonstrate a SPI parser vulnerability in KW520.

## What successful extraction would require

A controlled disclosure or execution primitive, not merely a corrupted screen or fault. Then a valid way to read protected flash under the chip's execution/protection rules. Code running from RAM is not automatically allowed to read protected internal flash; reusing normal internal-flash routines may matter. Finally an output path: if possible, copying recovered bytes into a separately verified unused SPI region would avoid requiring UART. The external dump proves erased space exists, not that the firmware never reserves or later uses it. No such region is approved for writes yet.

## Next bounded work

Develop offline diagnostic images that alter one known non-safety menu resource at a time and preserve the rest, once a reliable way to apply/read back SPI changes is available. First establish plain resource pointer redirection and literal-vs-format behavior using valid-size data, before any malformed-length tests. Record exact changed bytes and restore image. Actual parser behavior cannot be deduced solely from the resource data without MCU code or physical execution of the altered resource.

## Public references and applicability

- SEGGER SPI Flash: https://kb.segger.com/SPI_Flash — describes direct access and indirect MCU-RAM helpers. Relevant as a possible transport, not proof of access under AT32 protection.
- NXP CVE-2022-22819 bulletin: https://community.nxp.com/pwmxy87654/attachments/pwmxy87654/lpc%40tkb/226/3/NXP%20Security%20Bulletin-MCU_SB2_loader%20-%20Public.pdf — a documented external/update-data parser bug in other MCUs. Establishes this attack class exists, not an AT32 vulnerability.
- RT890 firsthand thread: https://www.mikrocontroller.net/topic/558990 — same MCU model with product-specific modified update/UART extraction report; no demonstrated applicability to KW520 SPI resources.
