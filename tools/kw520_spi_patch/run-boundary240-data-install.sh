#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--transition-224-to-240" ]] || { echo "Refusing: pass --transition-224-to-240" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary240-probe --from-allocation 224 --to-allocation 240 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary240-probe/boundary240-data-install.cfg --mode boundary240-data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '5001bc85e03cb004f7aaffd886810e550f7af51694099ac114475350c307221d' 'build/kw520-spi-patch/boundary240_data_install.bin' \
  'dda9adf54f387a17957b0a0337fd671e2cd48853fe3a6fcb107701a1d4b41b45' 'build/kw520-boundary240-probe/data-test-sector-00c000.bin' \
  'cf5a3b98cd5ff2b9611c503f9ebbf0b44241a05a9568ececa83cd28c3ea4fbff' 'build/kw520-boundary240-probe/boundary240-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary240-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary240-probe/boundary240-data-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (direct allocation-224 to allocation-240 transition verified|exact allocation-240 data sector already present; no write)" "$log"
