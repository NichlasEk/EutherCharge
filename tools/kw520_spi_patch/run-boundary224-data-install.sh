#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--transition-192-to-224" ]] || { echo "Refusing: pass --transition-192-to-224" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary224-probe --from-allocation 192 --to-allocation 224 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary224-probe/boundary224-data-install.cfg --mode boundary224-data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '8ed471602b8d7104e47fe8dc40145c991369f75a85745342531497d8243bffe3' 'build/kw520-spi-patch/boundary224_data_install.bin' \
  '6df7f0b56e7941a05b16b8be6e4297ed86eb17f09e4b6acb95a10128510d849b' 'build/kw520-boundary224-probe/data-test-sector-00c000.bin' \
  'bfb172dadd41a9f2f2fcbd0ecd4be16947566431230207ccfc7ded3df1df8274' 'build/kw520-boundary224-probe/boundary224-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary224-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary224-probe/boundary224-data-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (direct allocation-192 to allocation-224 transition verified|exact allocation-224 data sector already present; no write)" "$log"
