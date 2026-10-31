# KW520 fixed two-byte literal-rendering probe

This is deliberately not a generic SPI programmer. The SRAM helper has one
compiled-in mutation: EN25Q32 bytes `0x003899..0x00389a` may change from
`6d 65` (`me` in `Huvudmeny`) to `25 25` (`%%`). Both changes are 1-to-0 only,
so the probe uses Page Program and contains no sector, block or chip erase.

Before changing protection or issuing Page Program it requires all of the
following:

- live PA8/SPI2 configuration exactly matches the qualified charger state;
- mailbox arming word is `0x41524d31`;
- JEDEC ID is `1c 30 16`;
- status is exactly the installed value `0x18`;
- the block-protection read for sector `0x003000` is exactly `0xff`;
- the two target bytes are exactly `6d 65`.

The qualified EN25Q32(A/B) path clears BP2..BP0 by `06`, status-register write
`01 00`, and a ready poll. It then checks WEL after another `06`, emits one
`02 00 38 99 25 25` transaction, polls WIP, and reads the two bytes and full
sector CRC back. Finally it restores status `0x18` through `06` + `01 18` and
verifies the readback. Best-effort cleanup also attempts to restore `0x18` on
every post-unlock failure. There is no host-selected address, length or
payload. A successful state is `0x41`; every refusal/error has a distinct
state.

The physical result was `Huvud%%ny`: both percent bytes were rendered
literally. This proves that the installed firmware consumes this external
language payload, and rules out printf-like interpretation on this resource
path. It is not an internal-flash readout.

Do not execute this helper until a live readback of sector `0x003000` matches
SHA-256 `95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9`
and a separately tested fixed-sector restoration helper is ready.

`restore_sector.c` is that separate recovery binary. It requires arming word
`0x41524d32`, the same live pin/SPI/JEDEC/status/protection gates, an SRAM input
buffer at `0x20002100` whose CRC-32B is exactly `f5c23372`, and a current target
sector CRC of either `7985c2f6` (the exact two-byte probe) or `f5c23372` (already
restored). In the already-restored case it exits without Write Enable. Only the
exact patched case can issue fixed `20 00 30 00`, verify the erased-sector CRC,
write 16 fixed 256-byte pages from the gated buffer, and require final CRC
`f5c23372`. It contains no block erase, chip erase, generic address, or status-
register-write instruction other than the fixed `0x00` unlock and fixed
`0x18` restoration required for the qualified EN25Q32(A/B).

The physical restore build is linked at `0x20001a00`, uses mailbox
`0x20002000`, input buffer `0x20000a00–0x200019ff`, and stack top
`0x20002300`. This deliberately avoids the live DMA/peripheral window observed
at `0x20002380–0x200023f7` during the rejected sector-read attempts.

The complete physical cycle passed on 2026-10-31:

1. baseline sector CRC `f5c23372` and bytes `6d 65` were gated;
2. the fixed patch produced sector CRC `7985c2f6`;
3. a cold start displayed `Huvud%%ny`;
4. recovery erased only sector `0x003000`, programmed 16 fixed pages, and
   restored CRC `f5c23372` plus status `0x18`;
5. the final normal cold start displayed `Huvudmeny` and the UI worked.

Machine-readable evidence is in
`artifacts/kw520-jlink/20261031-spi-format-probe-cycle-complete.json`.
