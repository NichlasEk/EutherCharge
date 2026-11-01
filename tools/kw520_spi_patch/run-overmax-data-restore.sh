#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-overmax-data" ]]; then
  echo "Refusing: pass --restore-overmax-data to restore only sector 0x00c000 to all-FF" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_overmax_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-overmax-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-overmax-probe/overmax-data-restore.cfg --mode data-restore --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '0f9786eaba3c3589d2f60fb36723fe246f0a710a99185dc06e0167c69fd96044' 'build/kw520-spi-patch/overmax_data_restore.bin' \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-overmax-probe/data-original-sector-00c000.bin' \
  '8e3bf029ab27f0f5629123a7e2ab5d211ac574b82ddc843175918c4935749cc7' 'build/kw520-overmax-probe/overmax-data-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/overmax-data-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-overmax-probe/overmax-data-restore.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact overmax data sector restored to all-FF" "$log" && \
   ! grep -Fq "ACCEPTED: overmax data sector already all-FF; no write" "$log"; then
  echo "Overmax data-restore acceptance line missing" >&2
  exit 1
fi
