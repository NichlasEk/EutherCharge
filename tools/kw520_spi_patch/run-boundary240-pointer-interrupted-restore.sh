#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--recover-exact-status02-sector" ]] || { echo "Refusing: pass --recover-exact-status02-sector" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary240-probe --from-allocation 224 --to-allocation 240 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary240-probe/boundary240-pointer-interrupted-restore.cfg --mode boundary240-pointer-interrupted-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary_pointer_interrupted_restore.bin >/dev/null
printf '%s  %s\n' \
  '80da3ee0c38d3700a3be25d78c88f73d81d269167bdfb226488bb16e0a8acbf5' 'build/kw520-spi-patch/boundary_pointer_interrupted_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary240-probe/pointer-original-sector-003000.bin' \
  '4dfd7120b71fe5bc62cfb56940861aba0004a32259b78b71a2fa2bafe3c33e87' 'build/kw520-boundary240-probe/boundary240-pointer-interrupted-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary240-pointer-interrupted-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary240-probe/boundary240-pointer-interrupted-restore.cfg 2>&1 | tee "$log"
grep -Fq "ACCEPTED: interrupted pointer sector recovered and verified through bitbang SPI" "$log"
