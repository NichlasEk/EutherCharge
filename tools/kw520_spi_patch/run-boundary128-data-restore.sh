#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-boundary128-data" ]]; then
  echo "Refusing: pass --restore-boundary128-data to restore only sector 0x00c000 to all-FF" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary128_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary128-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary128-probe/boundary128-data-restore.cfg --mode boundary128-data-restore --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '844bea3b5b3ef045bd122a3a8ac76689b50ad12d938e26e06ec61701d3814687' 'build/kw520-spi-patch/boundary128_data_restore.bin' \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-boundary128-probe/data-original-sector-00c000.bin' \
  '6e20b7c9d480400fa77d881d81c232482dfffd87eab8ecf3bc91aa3665c73ea4' 'build/kw520-boundary128-probe/boundary128-data-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary128-data-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary128-probe/boundary128-data-restore.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: allocation-128 data sector restored to all-FF" "$log" && \
   ! grep -Fq "ACCEPTED: allocation-128 data sector already all-FF; no write" "$log"; then
  echo "Allocation-128 data-restore acceptance line missing" >&2
  exit 1
fi
