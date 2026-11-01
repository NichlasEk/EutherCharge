#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary128-data" ]]; then
  echo "Refusing: pass --write-boundary128-data to install only allocation 128 in sector 0x00c000" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary128_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary128-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary128-probe/boundary128-data-install.cfg --mode boundary128-data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '27971d864c839f819c38cd194290860b45f40cfc89452648db7097dbda1e6045' 'build/kw520-spi-patch/boundary128_data_install.bin' \
  '013758d6704cdab4d96c272a0f3c6749599a0e14a6826aec775867597cc84c16' 'build/kw520-boundary128-probe/data-test-sector-00c000.bin' \
  '42c79638d61fe796f673ee57e281c0b53af38a97af0e5664e5c570ae80428b4a' 'build/kw520-boundary128-probe/boundary128-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary128-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary128-probe/boundary128-data-install.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact allocation-128 data sector installed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact allocation-128 data sector already present; no write" "$log"; then
  echo "Allocation-128 data-install acceptance line missing" >&2
  exit 1
fi
