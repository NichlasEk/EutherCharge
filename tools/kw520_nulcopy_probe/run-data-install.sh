#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--install-nulcopy-data" ]] || { echo "Refusing: pass --install-nulcopy-data" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_nulcopy_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-nulcopy-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-nulcopy-probe/nulcopy-data-install.cfg --mode nulcopy-data-install --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/nulcopy_data_install.bin >/dev/null
printf '%s  %s\n' \
  '055157e4d1517777a90c27bb8000ccdbf56540e348bfa72a6802524d58fa313d' 'build/kw520-spi-patch/nulcopy_data_install.bin' \
  '854a916d18e4c13e75966754fd380c1d6f8cbbe530d637f995c4228b5e493738' 'build/kw520-nulcopy-probe/nulcopy-data-test-sector-00c000.bin' \
  '2956071e27fc51513544e68c629aa40e57723e4cdb9d381bf5f6a4bf1ee7548f' 'build/kw520-nulcopy-probe/nulcopy-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/nulcopy-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-nulcopy-probe/nulcopy-data-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact embedded-NUL data sector installed|exact embedded-NUL data sector already present; no write)" "$log"
