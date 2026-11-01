# KW520 protected-firmware self-disclosure findings

Date: 2026-11-01

Target: KONNWEI KW520, hardware 1.2.0, software 1.0.7

MCU: AT32F421C8T7, Cortex-M4, 64 KiB internal Flash, 16 KiB SRAM

External Flash: EN25Q32, 4 MiB, JEDEC `1c 30 16`

Purpose: external technical review and selection of the next bounded experiment

## Executive result

The target does not permit ordinary SWD readout or single-stepping of its
original main-Flash program while low-level FAP is active. Debug activation
causes a HardFault/lockup because main-Flash access is blocked in debug mode.
Disabling FAP is not acceptable because the protected-to-unprotected transition
mass-erases main Flash.

The viable route is therefore to keep the original firmware normally booted
from main Flash and make it disclose data through an output that survives long
enough to capture. This route has already produced one real disclosure:

- controlled external string bytes select the original firmware's internal
  glyph renderer;
- the renderer writes the resulting pixels into SRAM;
- a subsequent J-Link SRAM capture recovers those pixels exactly;
- all 128 high-byte glyphs `0x80..0xff` were recovered as 768 exact bytes;
- the matching font/icon table is absent from the external Flash and retained
  updater files, so the table is most likely in protected MCU Flash.

This is a fixed internal-asset oracle, not yet an arbitrary-address firmware
read primitive.

## Current physical state

The apparatus is restored and normally bootable:

- pointer sector `0x003000` CRC-32B: `f5c23372`;
- inactive data sector `0x00c000` all-FF CRC-32B: `f154670a`;
- EN25Q32 status restored to `0x18`;
- zero SPI helper errors;
- final cold-start observation: `Huvudmeny`, buttons responsive.

Raw SRAM dumps and proprietary derived glyph binaries remain ignored under
`build/` and are not part of this shareable report.

## Protection behavior already established

1. SWD DPIDR is readable and the Cortex-M4 can be halted.
2. SRAM can be read, written, executed and restored while the original program
   is no longer running.
3. A debugger-loaded SRAM helper can use SPI2 and PA8 to read the external
   EN25Q32 reliably.
4. Direct SWD reads of protected main Flash return zero.
5. A DMA SRAM-to-SRAM positive control succeeds, while the same DMA channel
   reading `0x08000000` completes without an error but returns zero.
6. Branching from debugger-loaded SRAM to candidate main-Flash routines did not
   yield a copy or return, even after the target observed debug detach.
7. FAP remains enabled. No unlock, option-byte change, internal-Flash erase or
   internal-Flash program has been attempted.

Artery's access table says that low-level protected main Flash is inaccessible
in debug mode or when booted/executing from SRAM, but remains accessible to the
normally booted main-Flash program. That distinction is the basis of the
self-disclosure strategy.

## External resource path controlled so far

The external Flash contains a language directory and eight language banks.
Ordinary text records use a big-endian 16-bit allocation/length including the
terminating NUL. A big-endian 32-bit pointer table stores offsets relative to
the language-directory base at external offset `0x003200`.

The main-title resource can be redirected to a controlled record in unused
external sector `0x00c000`. All modifications used exact CRC-gated helpers and
were restored pointer-first.

Verified runtime SRAM path:

```text
external EN25Q32 record
        |
        v
source buffer                 0x20003978
source pointer storage        0x20003974
source end pointer storage    0x20003710
        |
        v
transient render copy         0x20003728
render destination pointer    0x20003714
        |
        v
LCD backing canvas            0x20000000..0x200007ff
```

The source/end behavior was measured with normal `Huvudmeny` and controlled
`SAFEWXYZ`. Only the expected title bytes and a few layout/end values changed
inside the two identified SRAM objects.

## Parser boundaries and closed leads

### Ordinary-string copy cap

- The largest original record allocation is 113 bytes.
- Allocation 114 was accepted and all 113 visible bytes plus NUL appeared at
  `0x20003978`.
- Allocation 256 copied exactly 256 controlled bytes.
- Allocation 320 still copied only bytes 0..255 and wrote NUL at offset 256.
- Increasing allocations to 384..512 therefore cannot move this boundary
  toward the stack.

An early embedded NUL did not stop the 256-byte copy. The firmware copied all
256 allocation bytes, including bytes after the NUL, and then terminated its
internal buffer.

### Apparent control word did not qualify

Payload offsets 252..255 overlap a recurrent code-shaped SRAM word. The value
was changed to the Thumb address of a controlled SRAM marker stub, but no
mailbox magic appeared either after boot or after a button event. It is not a
qualified return address or control-flow primitive. Blind address sweeps were
stopped.

### Other parser leads

- Percent bytes render literally; no format-string sink was demonstrated.
- Extending the language directory to nine entries still produced an internal
  count of eight and displaced one existing ID instead of overflowing it.
- The updater services and retained UPLINK/BTLINK installers yielded no KW520
  firmware image.
- External Flash contains no ordinary Cortex-M vector image and no matching
  uncompressed internal glyph table.

## Framebuffer result

The first 2,048 SRAM bytes are a `128x128` one-bit backing canvas:

```text
address = 0x20000000 + page_y * 128 + x
pixel   = (byte >> (y % 8)) & 1
```

The physical `128x64` LCD is canvas rows 24..87, corresponding to pages 3..10.
Rows 0..23 contain non-displayed prior/work data.

This geometry was not guessed from a photograph. The paired full-SRAM captures
reconstruct exact `Huvudmeny` and exact `SAFEWXYZ` while the rest of the screen
remains identical. Decoder: `tools/kw520_framebuffer.py`.

The framebuffer is therefore a useful exact output channel, but it is not by
itself a raw-memory window. The renderer currently transforms an 8-bit glyph
index into a six-column bitmap before writing pixels.

## Internal glyph/asset disclosure

Controlled static pages placed every high-byte value in known screen cells.
Read-only SRAM captures then recovered each rendered cell without camera or OCR
error.

- covered codes: every value `0x80..0xff`, exactly once;
- recovered glyphs: 128;
- bytes per glyph: 6 column bytes, LSB-top;
- total exact internal asset bytes: 768;
- corrected complete-table SHA-256:
  `75b9cd129912998c50dfd283973d458d89657b1f32ac325c2beeedd0adbabf4f`;
- atlas SHA-256:
  `6271a1ff72da81a4e8c76c138c33b3ff36d5a98d2046228f7f77355f253e3598`.

The `0xc0..0xff` region follows ISO-8859-1 ordering. The `0x80..0x9f` region
contains coherent UI icons and line assets. A corrected search scanned 11,397
local files in nine byte/bit/column representations and found neither the full
table nor any nontrivial 16-glyph group outside the derived output.

The public reproduction chain is `tools/kw520_framebuffer.py` for decoding the
SRAM canvas, `tools/extract_kw520_glyphs.py` for exact six-byte cells and
`tools/combine_kw520_glyphs.py` for strict `0x80..0xff` coverage. Their three
focused test modules use synthetic inputs and require no proprietary dump.

What this proves: normally booted protected firmware can be used as a fixed
asset oracle and SRAM/LCD can exfiltrate the result exactly.

What this does not prove: control over the internal font base, an index wider
than eight bits, a caller-supplied MCU address, or arbitrary code-byte readout.

## Cross-capture SRAM stack-frame analysis

`tools/analyze_kw520_sram_frames.py` scanned 21 retained 16-KiB SRAM captures
for aligned Cortex-M basic exception-frame shapes. The strict scan requires:

- xPSR Thumb bit set;
- a small IPSR value;
- even PC inside `0x08000000..0x0800ffff`;
- odd LR inside the same main-Flash range.

It found 11 frame-shaped candidates. These can be current frames, stale stack
frames or coincidental data. They do not contain instruction bytes and their PC
values are not proven function entries. Full metadata:
`artifacts/kw520-jlink/20261101-sram-frame-candidates.json`.

The most repeatable cluster is:

| SRAM address | LR | observed PCs | captures |
|---|---|---|---|
| `0x20003630/0x20003680` | `0x0800a9dd` | `0x0800aac8`, `0x0800aada`, `0x0800aaea`, `0x0800aafa` | four menu/language/glyph captures |

This tight PC progression and repeated LR make the region around
`0x0800a9dc..0x0800aafa` the strongest code-location correlation in the current
SRAM evidence. It is likely associated with a frequently repeated menu/render
path, but that role is not yet proven.

One glyph-page-2 candidate is especially suggestive:

```text
frame address  0x20003b90
r0             0x000000ff
r1             0x20000005
r2             0x00000003
r3             0x00000003
r12            0x20003b44
lr             0x0800a04d
pc             0x0800f40a
xpsr           0x21000000
```

`r0 == 0xff` matches the last controlled glyph code and `r1` points five bytes
into the framebuffer. This is an attractive renderer hypothesis, but it is a
single correlation and must not be treated as proof.

Other repeated LR clusters are `0x08008037` and `0x0800012b`. The scanner's
output records every candidate and capture hash so an external reviewer can
apply stricter or alternative frame criteria without needing raw dumps.

## Best next self-disclosure experiments

### Priority 1: low/control-byte renderer census

The high-byte domain is exhausted and fixed. The next bounded input surface is
`0x01..0x7f`, with special attention to `0x01..0x1f` and `0x7f`.

Goal: determine whether any byte is an escape, icon-bank selector, font switch,
width/stride control or multi-byte drawing command. If a control byte changes
renderer state or consumes following bytes as parameters, it may expose a base,
page, stride or alternate asset table that the high-byte test cannot reach.

Acceptance should use static known-position pages plus exact SRAM framebuffer
capture, not video interpretation. NUL remains excluded except as terminator.

### Priority 2: deterministic frame sampling around rendering

Repeat normal cold boot with one minimal changing glyph and activate debug at
several well-defined points of its scroll/update cycle. Each activation freezes
the target, so every sample requires a cold restart. Correlate only frame-shaped
PC/LR/register values that move with the controlled glyph or screen phase.

The aim is not to single-step protected Flash. It is to turn the FAP-induced
fault into a crude sampling profiler of the last normally executing context.

### Priority 3: identify another renderer/resource class

External offset `0x000000` is a verified `128x32` one-bit logo resource, but
changing it did not affect the observed startup screen. Locate the UI state or
condition that consumes it. A bitmap/blit path may expose width, stride, source
or destination parameters that the six-byte glyph path does not.

### Stop conditions

Stop and restore immediately on:

- a test-sector or pointer CRC outside the predeclared pair;
- failed SPI verification or nonzero helper error;
- loss of normal menu/button behavior after pointer-first recovery;
- any proposal to disable FAP, alter option bytes or mass-erase main Flash;
- a crash without a separately observed disclosure/control marker.

## Questions for an external reviewer

1. Does the repeated `LR=0x0800a9dd`, `PC=0x0800aac8..0x0800aafa` cluster look
   like a plausible Thumb loop/call-site pattern when only addresses and ABI
   registers are available?
2. Can the FAP-induced HardFault be triggered or sampled in a way that more
   reliably preserves the last normally executing basic frame without entering
   ordinary debug execution?
3. Does the `r0=0xff`, `r1=0x20000005` frame suggest a common embedded-font ABI
   or framebuffer primitive worth testing?
4. Are there known 6x8 embedded font tables matching the recovered SHA/fingerprint
   under a representation not covered by raw, reversed, inverted, padded and
   row-major scans?
5. What bounded byte sequence is most likely to discriminate an ordinary glyph
   table from a renderer escape/control grammar without relying on a crash?
6. Are there AT32F421-specific normally-booted peripherals or ROM routines that
   can copy main Flash to SRAM while preserving main-Flash execution origin and
   then expose the result without enabling debug mode?

## Shareable evidence index

- `artifacts/kw520-jlink/20261101-runtime-sram-string-path.json`
- `artifacts/kw520-jlink/20261101-static-glyph-pages.json`
- `artifacts/kw520-jlink/20261101-sram-frame-candidates.json`
- `artifacts/kw520-jlink/20261101-dma-flash-read-discriminator.json`
- `artifacts/kw520-jlink/20261101-call-oracle-detach18.json`
- `docs/kw520-ram-read-bridge-20261031.md`
- `docs/kw520-jlink-spi-extraction-plan.md`
- `docs/resource-format.md`

Official protection reference:

- <https://www.arterytek.com/download/Program%20and%20Debug/UM_ISP_Programmer_EN.pdf>
- <https://arterytek.com/en/product/AT32F421.jsp>
