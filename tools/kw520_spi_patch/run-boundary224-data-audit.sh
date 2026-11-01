#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--read-only-sector-audit" ]]; then
  echo "Refusing: pass --read-only-sector-audit for the fixed 0x00c000 CRC read" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary224-probe --from-allocation 192 --to-allocation 224 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary224-probe/boundary224-data-audit.cfg --mode boundary224-data-audit --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  'b84170c42716410453f397b18a4c4ca1d5b725b4a78267be000046179197fbed' 'build/kw520-spi-patch/boundary_data_audit.bin' \
  '6190f192cf0346aff5f7dc2ce0de5c7819e8d9ecaf496830a301ef4ad86226cd' 'build/kw520-boundary224-probe/data-previous-sector-00c000.bin' \
  '83a3a3bababbac6489c3dfbf0dfa73ee00ff0db8b43b8d0989d52627d01e4dd8' 'build/kw520-boundary224-probe/boundary224-data-audit.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary224-data-audit-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary224-probe/boundary224-data-audit.cfg 2>&1 | tee "$log"
grep -Fq "ACCEPTED: read-only allocation-224 data-sector audit completed" "$log"
