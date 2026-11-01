#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-boundary224-pointer" ]] || { echo "Refusing: pass --restore-boundary224-pointer" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary224-probe --from-allocation 192 --to-allocation 224 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary224-probe/boundary224-pointer-restore-retry.cfg --mode boundary224-pointer-restore-retry --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  'cf9a39d3e1b42dc3011143cce501f248bffa0167793b9f23f4d866be3b82eaae' 'build/kw520-spi-patch/boundary128_pointer_restore_retry.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary224-probe/pointer-original-sector-003000.bin' \
  '1f0f060971286fb04864c5278a1d172fea1ad97667fb49b73611254535f9128d' 'build/kw520-boundary224-probe/boundary224-pointer-restore-retry.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary224-pointer-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary224-probe/boundary224-pointer-restore-retry.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (allocation-224 title pointer restored with bounded status retry|original title pointer already present; bounded helper made no write)" "$log"
