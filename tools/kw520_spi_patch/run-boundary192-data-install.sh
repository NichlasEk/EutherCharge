#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--transition-160-to-192" ]]; then
  echo "Refusing: pass --transition-160-to-192 for the fixed inactive-sector transition" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary192-probe --from-allocation 160 --to-allocation 192 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary192-probe/boundary192-data-install.cfg --mode boundary192-data-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  'b8982c9a07112ffeda393431f40de08a935e0fc2026848b1b873b6c014199da5' 'build/kw520-spi-patch/boundary192_data_install.bin' \
  '6190f192cf0346aff5f7dc2ce0de5c7819e8d9ecaf496830a301ef4ad86226cd' 'build/kw520-boundary192-probe/data-test-sector-00c000.bin' \
  '16b2666368585ac071521cfd518ec2a31dc0b662742d67a5a5fd76358313b029' 'build/kw520-boundary192-probe/boundary192-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary192-data-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary192-probe/boundary192-data-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (direct allocation-160 to allocation-192 transition verified|exact allocation-192 data sector already present; no write)" "$log"
