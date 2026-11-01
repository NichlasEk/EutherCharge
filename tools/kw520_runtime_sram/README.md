# KW520 runtime SRAM capture

This gate takes one read-only 16 KiB MEM-AP snapshot of the AT32F421 SRAM. It
does not contain target SRAM writes, flash commands, reset or resume commands.
OpenOCD debug initialization is nevertheless known to freeze the protected
original firmware, so the charger must be cold-started after every capture.

Run it only with an unused lowercase label:

```sh
./tools/kw520_runtime_sram/run-capture.sh --capture <label>
```

The script refuses to replace an existing dump or log, requires OpenOCD's
acceptance line and requires the output size to be exactly 16,384 bytes. Raw
SRAM dumps remain under ignored `build/kw520-runtime-sram/`; publish only the
minimum hashes, addresses and byte-difference evidence needed for the research
result.
