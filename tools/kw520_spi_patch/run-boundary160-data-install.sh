#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--transition-128-to-160" ]]; then
  echo "Refusing: pass --transition-128-to-160 for the CRC-locked inactive data-sector transition" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary160_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary160-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary160-probe/boundary160-data-install.cfg --mode boundary160-data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '0f3800b300552d3abab05f371c01a859e1cf9ece36fa66413c34c2170f5e337b' 'build/kw520-spi-patch/boundary160_data_install.bin' \
  '4b8c14f8008e650fdfd8cdb679451d4bab2d69898eb43d55ea40c068c28fdfe7' 'build/kw520-boundary160-probe/data-test-sector-00c000.bin' \
  '63f083cf8d2d7e4d4b63c83bbb63c59e3a8612f137c34b63c6f0ce6fae5179c8' 'build/kw520-boundary160-probe/boundary160-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary160-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary160-probe/boundary160-data-install.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: direct allocation-128 to allocation-160 transition verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact allocation-160 data sector already present; no write" "$log"; then
  echo "Allocation-160 data-install acceptance line missing" >&2
  exit 1
fi
