#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary-baseline" ]]; then
  echo "Refusing: pass --write-boundary-baseline to install only the fixed SAFE baseline" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_boundary_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-boundary-probe --force >/dev/null
python tools/prepare_kw520_boundary_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-boundary-probe/boundary-baseline.cfg --mode baseline --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '395858da02d72f744be32921852bef6e427948840b2fd57bf1b0002e90a6427e' 'build/kw520-spi-patch/boundary_baseline.bin' \
  '99ee10a85823906ad209726304556effedb605c37f3a3270e60250a4fecf82f0' 'build/kw520-boundary-probe/baseline-sector-003000.bin' \
  'bdae26401e2d85da64db464b42bdffd87e02713c32d1051b5408ba8ee78568ef' 'build/kw520-boundary-probe/boundary-baseline.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/boundary-baseline-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary-probe/boundary-baseline.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact boundary baseline programmed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact boundary baseline already present; no write" "$log"; then
  echo "Boundary-baseline acceptance line missing; target state is not accepted" >&2
  exit 1
fi
