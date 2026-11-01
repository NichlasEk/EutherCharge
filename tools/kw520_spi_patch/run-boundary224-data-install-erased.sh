#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--install-224-from-audited-erased" ]]; then
  echo "Refusing: pass --install-224-from-audited-erased" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary224-probe --from-allocation 192 --to-allocation 224 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary224-probe/boundary224-data-install-erased.cfg --mode boundary224-data-install-erased --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '8f12c9bb38dc63a097b6e9f21deb98581415d021b31dccd48af0ff2a33cbea28' 'build/kw520-spi-patch/boundary224_data_install_erased.bin' \
  '6df7f0b56e7941a05b16b8be6e4297ed86eb17f09e4b6acb95a10128510d849b' 'build/kw520-boundary224-probe/data-test-sector-00c000.bin' \
  '9a9a0f733529f8c599b7f2ec83068114ac3a884e2b614224a6a687f2732f0a92' 'build/kw520-boundary224-probe/boundary224-data-install-erased.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary224-data-install-erased-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary224-probe/boundary224-data-install-erased.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (allocation-224 installed from audited all-FF sector|exact allocation-224 data sector already present; no write)" "$log"
