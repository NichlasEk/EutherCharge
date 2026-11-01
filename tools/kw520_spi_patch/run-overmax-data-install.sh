#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-overmax-data" ]]; then
  echo "Refusing: pass --write-overmax-data to install only the fixed record in sector 0x00c000" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_overmax_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-overmax-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-overmax-probe/overmax-data-install.cfg --mode data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '5b90951a7c0b645239fdc2066bcd2a0e94850c831a1930d7388e5a9879f46e19' 'build/kw520-spi-patch/overmax_data_install.bin' \
  '2698046d4af56aa01eea3e2f6a6e2b54df29bcb8c1d969963e0f87c9a6caaf09' 'build/kw520-overmax-probe/data-test-sector-00c000.bin' \
  '1713fb48e5be80d30351b5924af39fb20fa0816fe0ad0bb1ddb1436e07853d57' 'build/kw520-overmax-probe/overmax-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/overmax-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-overmax-probe/overmax-data-install.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact overmax data sector installed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact overmax data sector already present; no write" "$log"; then
  echo "Overmax data-install acceptance line missing" >&2
  exit 1
fi
