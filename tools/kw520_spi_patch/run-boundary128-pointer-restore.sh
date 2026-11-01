#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-boundary128-pointer" ]]; then
  echo "Refusing: pass --restore-boundary128-pointer to restore only the original title pointer" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary128_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary128-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary128-probe/boundary128-pointer-restore.cfg --mode boundary128-pointer-restore --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '5b6a5a1a687764ece1f3783b80fa0fea847fd73d2457442b74b80ebc814c28b1' 'build/kw520-spi-patch/overmax_pointer_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary128-probe/pointer-original-sector-003000.bin' \
  '7152a7e9700c5cb4beeb7a532ae6080548f6a6de06b7eb89c37688a95dcaaef7' 'build/kw520-boundary128-probe/boundary128-pointer-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary128-pointer-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary128-probe/boundary128-pointer-restore.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact allocation-128 title pointer restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original title pointer already present; no write" "$log"; then
  echo "Allocation-128 pointer-restore acceptance line missing" >&2
  exit 1
fi
