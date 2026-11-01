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

## Qualified same-bank pointer probe

`prepare_kw520_pointer_probe.py` prepares the discriminator without touching
hardware. It changes only table entry 1 at `0x003604` from relative
record pointer `0x00000692` (`Huvudmeny`) to the already valid entry-2 pointer
`0x0000069e` (`Testa`). The record bytes and both length prefixes remain
unchanged. The expected physical result is a main-menu title of `Testa`.

The single changed pointer byte is `0x92 -> 0x9e`, which includes NOR 0-to-1
transitions. Therefore this probe must never use Page Program alone. The
separately built `pointer_probe.bin` reuses the qualified fixed-sector engine
but has distinct magic `KWPD`, arm word `ARM5`, input CRC `14b0524b`, required
live target CRC `f5c23372`, and final CRC `14b0524b`. It can only erase and
replace sector `0x003000` with the one CRC-gated 4 KiB SRAM payload. A physical
OpenOCD gate is intentionally separate from the offline generator and must
retain exact SRAM backup/readback/restoration checks.

`prepare_kw520_pointer_openocd.py` derives that gate from the exact physically
qualified restore config and refuses if the template SHA-256 changes. The run
script also requires the explicit argument `--write-pointer-probe`, regenerates
the CRC-locked payload and config, and exits nonzero unless OpenOCD prints one
of the two exact accepted outcomes. This is still only preparation until the
physical run and subsequent LCD observation have both occurred.

The forward helper is paired with a separately compiled `pointer_restore.bin`:
magic `KWRO`, arm word `ARM6`, restore-buffer CRC `f5c23372`, required patched
target CRC `14b0524b`, and final CRC `f5c23372`. It cannot accept the earlier
percent probe or an unknown sector. `run-pointer-restore.sh` likewise requires
the explicit `--restore-pointer-probe` argument. Keep this helper and the four
original-sector chunks available before authorizing the forward experiment.

The complete physical cycle passed on 2026-10-31. The forward run accepted
original CRC `f5c23372`, programmed 16 pages, verified pointer-sector CRC
`14b0524b`, and restored status `0x18`. A normal cold start displayed `Testa`.
The ARM6 run then accepted only CRC `14b0524b`, restored original CRC
`f5c23372` plus status `0x18`, and a final cold start displayed working
`Huvudmeny`. This proves same-bank table-pointer following. It does not prove
cross-bank access, an out-of-bounds read, or internal-flash disclosure.

Machine-readable evidence is in
`artifacts/kw520-jlink/20261031-spi-pointer-probe-cycle-complete.json`.

## Qualified valid cross-bank pointer probe

The next bounded discriminator redirects the same table entry from relative
pointer `0x00000692` (`Huvudmeny`, record `0x003892`) to relative pointer
`0x000013e9` (`Menu principal`, existing Français record `0x0045e9`). Only
pointer bytes at `0x003606..0x003607` differ; neither record nor a length prefix
is modified. The fixed sector CRC is `b29ee7d1`.

The forward pair uses magic `KWCB`/`ARM7`, requires live original CRC
`f5c23372`, input CRC `b29ee7d1`, and final CRC `b29ee7d1`. Its recovery pair
uses `KWCR`/`ARM8`, accepts only live CRC `b29ee7d1`, input CRC `f5c23372`, and
final CRC `f5c23372`. Both are compiled from the already qualified fixed-sector
engine. The restore helper must pass a physical no-op qualification on the
original sector before the forward write is authorized.

The complete physical cycle passed on 2026-10-31. The forward run verified
CRC `b29ee7d1`; a cold start displayed `Menu principal`. ARM8 then restored
CRC `f5c23372` and status `0x18`; the final cold start displayed working
`Huvudmeny`. This proves that the relative ordinary-string pointer is not
confined to the active language bank. It remains an in-range external-flash
read, not an out-of-bounds or internal-flash disclosure.

Machine-readable evidence is in
`artifacts/kw520-jlink/20261031-spi-crossbank-probe-cycle-complete.json`.

## Qualified declared-length shortening

The next probe changes only the main-title record's big-endian allocation from
`0x000a` to `0x0008` at `0x003892`; payload `Huvudmeny\0` remains byte-exact.
The only changed byte is `0x0a -> 0x08`, a NOR-safe 1-to-0 transition, so the
forward `KWLN`/`ARM9` helper uses one fixed two-byte Page Program and no erase.
It requires original sector CRC `f5c23372` and final CRC `5e1e3b15`.

The separate `KWLR`/`ARMA` recovery helper accepts only live CRC `5e1e3b15`,
the exact original 4 KiB payload CRC `f5c23372`, and final CRC `f5c23372`. It
must pass a physical no-op qualification before the forward probe. The length
only decreases; an extension is deliberately not part of this experiment.

The complete physical cycle passed on 2026-11-01. With declared length 8 and
unchanged payload `Huvudmeny\0`, two independent cold starts displayed exactly
`Huvudmen`. ARMA then restored sector CRC `f5c23372` and status `0x18`; the
final cold start displayed working `Huvudmeny`. Thus this path uses the declared
length as the visible payload-byte boundary rather than relying only on the
stored NUL. This says nothing yet about the safety of length extension.

Machine-readable evidence is in
`artifacts/kw520-jlink/20261101-spi-length-probe-cycle-complete.json`.
