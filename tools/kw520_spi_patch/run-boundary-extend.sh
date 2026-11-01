#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary-extension" ]]; then
  echo "Refusing: pass --write-boundary-extension to change only fixed length 4 -> 8" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_boundary_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-boundary-probe --force >/dev/null
python tools/prepare_kw520_boundary_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-boundary-probe/boundary-extend.cfg --mode extend --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  'd427a74f5a1540b1e408a6719ac6f4cfb160ba4c30a0ed7ebe65199000ff1463' 'build/kw520-spi-patch/boundary_extend.bin' \
  'ccac1e14b676aa05a4dbf28eb7ff6d5938117bbdcd68d5b0f3fdd6fd65c692c7' 'build/kw520-boundary-probe/extended-sector-003000.bin' \
  '1219f08135d2c60b3d6b67eb01f2bcdb540a6e5a464102861475e615aff96171' 'build/kw520-boundary-probe/boundary-extend.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/boundary-extend-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary-probe/boundary-extend.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact boundary length extension programmed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact boundary extension already present; no write" "$log"; then
  echo "Boundary-extension acceptance line missing; target state is not accepted" >&2
  exit 1
fi
