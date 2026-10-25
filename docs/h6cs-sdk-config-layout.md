# SDK configuration field layout — 2026-10-25

Manufacturer SDK inspection located `NY8ConfigBlockConverter`, including a
NY8B062D-specific reader which uses `NY8CommonItemsReader`. This consumes a
configuration block using the device's ConfigSizeInWord ×2bytes and a little-endian
16-bit RegisterHelper. These offsets are **within an SDK configuration block**;
they are not physical programming addresses or offsets in the charger ROM.

`Nyquest.Core.dll` SHA256:
`41f71c7c1db0ab9ab651c9f192ec5c9f93f382bfbe2594770d0363d92f102eaf`.
SDK origin/extraction is recorded in `h6cs-regis-cpu-audit.md`. Vendor binaries and
disassembly remain outside Git. No original firmware bytes were used by the probe.

## Independently exercised layout

| SDK field | Word offset | Bits | Meaning indicated by SDK metadata |
|---|---:|---:|---|
| wdtReg |0|8|Watchdog enable field|
| wdtEventReg |0|9|Watchdog event selection|
| wdtTimeBaseReg |6|5:4|Watchdog base period selection|
| rdPortTypeReg |8|10|Port read-source selection|
| instClockReg |0|6|Instruction-clock field|
| instructionClockReg |0|7|Instruction-period field|

`tools/h6cs_sdk_config_probe.cs` instantiates only the converter's register metadata
and RegisterHelper, using an uninitialized dummy device object. It tests each field
against512one-hot input bits:3,072vendor-library evaluations total. It does not call
a writer, open a ROM, load chip data or attempt hardware access. Run in bubblewrap
with no network, private `/dev`, and read-only SDK mount:

```sh
mkdir -p build/h6cs-config
mcs -out:build/h6cs-config/probe.exe tools/h6cs_sdk_config_probe.cs
bwrap --unshare-net --ro-bind /usr /usr --ro-bind /etc /etc \
  --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 \
  --dev /dev --proc /proc --tmpfs /tmp \
  --ro-bind /tmp/h6cs-nyasm/app /sdk \
  --ro-bind "$PWD/build/h6cs-config" /work --chdir /work \
  /usr/bin/mono /work/probe.exe /sdk
node --test tests/h6cs-sdk-config.test.mjs
```

The committed golden fixture contains only synthetic field-test results. The
independent JS extractor matches every input bit in its18-byte field window;
combined-field and invalid-size tests also pass. It deliberately reports raw field
values, without guessing option polarity, full block size, checksum or file header.
It rejects a4096-byte ROM passed as its input. It is not wired into emulator reset
or automatic ROM loading.

## What this does and does not establish

This establishes the SDK's raw field positions and a reproducible way to inspect
future independently identified config blocks. It does not establish original
charger settings or that its reserved07FE/07FF words contain these fields. A
complete vendor config-file envelope and physical readback format are still not
verified. Distinguish SDK representation from chip storage/programming layout.

The earlier binary `.IC` profile yielded no plain-text map. `monodis` could list
metadata but full disassembly stopped on a missing WPF dependency. `ikdasm` read
the complete IL without installing WPF; the bounded probe above then verified the
field positions by executing the actual register helper in isolation.

Next: identify the SDK file envelope/config-version and device configuration size,
then determine whether any existing saved capture contains a matching separate
block. No further hardware acquisition is authorized by this offline work.

## Full block size and decoded option verification

The embedded `mask` resource identifies NY8B062D with config_size_word=0x10:
16little-endian words,32bytes. Its standard conversion context reports version3.
`tools/h6cs_sdk_config_decode_probe.cs` loads the real model through MaskRomLoader,
then invokes the actual NY8B062D reader on32synthetic combinations. Every read
succeeds. This validates meanings as well as field positions:

- WDT field0/1: disabled/enabled.
- Event field0/1: interrupt/reset.
- Time-base field0/1/2/3:250/60/3.5/15ms.
- Read-source field0/1: output register/pin.

The standalone decoder accepts exactly32bytes and explicit config version3;
unsupported versions and ROM-sized input are rejected. It decodes only these
verified fields, not oscillator frequency or every configuration option. It does
not locate or authenticate a config block inside a firmware container, nor infer
physical programming addresses. It is not connected to automatic ROM loading.

Compile the decode probe with mcs and run it using the same isolated command as
above, substituting decode.exe and passing /sdk. Its synthetic output is captured
in `tests/fixtures/h6cs/sdk-config-decoded.json`; all32cases match the JS decoder.
Four SDK-config tests now pass. No original configuration block has been located;
a filename search of the charger readout/probe directories found no config/CB/HEX
candidate. This is not an exhaustive content-level proof of absence.
