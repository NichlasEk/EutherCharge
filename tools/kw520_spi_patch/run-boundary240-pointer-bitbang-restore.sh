#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--recover-exact-partial-pointer-sector" ]] || { echo "Refusing: pass --recover-exact-partial-pointer-sector" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary240-probe --from-allocation 224 --to-allocation 240 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary240-probe/boundary240-pointer-bitbang-restore.cfg --mode boundary240-pointer-bitbang-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary_pointer_bitbang_restore.bin >/dev/null
printf '%s  %s\n' \
  '2fdce255bb48bd5f91e4d49d3d99bbab3624590e2f33a54d600bdd14e5601d8b' 'build/kw520-spi-patch/boundary_pointer_bitbang_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary240-probe/pointer-original-sector-003000.bin' \
  'e1b8095c9098ddf6defe54b5dff29682d5c43af5ee6fbb55a9a5637d2eb7a088' 'build/kw520-boundary240-probe/boundary240-pointer-bitbang-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary240-pointer-bitbang-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary240-probe/boundary240-pointer-bitbang-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (partial pointer sector recovered and verified through bitbang SPI|original pointer sector already present; recovery helper made no write)" "$log"
