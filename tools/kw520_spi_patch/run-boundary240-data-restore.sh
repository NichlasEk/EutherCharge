#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-boundary240-data" ]] || { echo "Refusing: pass --restore-boundary240-data" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary240-probe --from-allocation 224 --to-allocation 240 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary240-probe/boundary240-data-restore.cfg --mode boundary240-data-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary240_data_restore.bin >/dev/null
printf '%s  %s\n' \
  'ce17ffe82e2eec12c961789fb9d04166457590c52a301f5a764363fc79447239' 'build/kw520-spi-patch/boundary240_data_restore.bin' \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-boundary240-probe/data-original-sector-00c000.bin' \
  'a82b3413477e7553523fd827dca14cc5fa11b792f75f005520d657836e3699db' 'build/kw520-boundary240-probe/boundary240-data-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary240-data-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary240-probe/boundary240-data-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (allocation-240 data sector restored to exact all-FF|allocation-240 data sector already exact all-FF; no write)" "$log"
