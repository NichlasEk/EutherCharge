#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--install-language9" ]] || { echo "Refusing: pass --install-language9" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_language_gate.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-language-gate --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-language-gate/language9-install.cfg --mode language9-install --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/language9_install.bin >/dev/null
printf '%s  %s\n' \
  '9a7089953fb0795251a23810b5dc4eec9f002c1a5bf519cb951955771a41f2e1' 'build/kw520-spi-patch/language9_install.bin' \
  'e6d5eb146469e92b92440bd057a2b44d269bd46247ed4850907d13b630e413a5' 'build/kw520-language-gate/language9-test-sector-003000.bin' \
  '0d88a3759fe3531ac9918ff8852daf44a818f3e93c83840d0ff9d2a301a8e2b3' 'build/kw520-language-gate/language9-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/language9-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-language-gate/language9-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact valid language-9 directory sector installed|exact language-9 directory sector already present; no write)" "$log"
