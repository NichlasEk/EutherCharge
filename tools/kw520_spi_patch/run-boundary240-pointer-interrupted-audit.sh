#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--read-only-status02-audit" ]] || { echo "Refusing: pass --read-only-status02-audit" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary240-probe --from-allocation 224 --to-allocation 240 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary240-probe/boundary240-pointer-interrupted-audit.cfg --mode boundary240-pointer-interrupted-audit --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary_pointer_interrupted_audit.bin >/dev/null
printf '%s  %s\n' \
  'cd4741d81bc5a508f222479890a733feb75567f25849664f16f9e1f42e8f6c8c' 'build/kw520-spi-patch/boundary_pointer_interrupted_audit.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary240-probe/pointer-original-sector-003000.bin' \
  '042f5f8778a3224d79dd0957c4c14d47c8de9232ce999bfec948afd85e26d65f' 'build/kw520-boundary240-probe/boundary240-pointer-interrupted-audit.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary240-pointer-interrupted-audit-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary240-probe/boundary240-pointer-interrupted-audit.cfg 2>&1 | tee "$log"
grep -Fq "ACCEPTED: read-only interrupted pointer-sector audit completed" "$log"
