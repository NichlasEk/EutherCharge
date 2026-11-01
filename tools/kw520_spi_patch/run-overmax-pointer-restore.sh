#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-overmax-pointer" ]]; then
  echo "Refusing: pass --restore-overmax-pointer before restoring the data sector" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_overmax_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-overmax-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-overmax-probe/overmax-pointer-restore.cfg --mode pointer-restore --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '5b6a5a1a687764ece1f3783b80fa0fea847fd73d2457442b74b80ebc814c28b1' 'build/kw520-spi-patch/overmax_pointer_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-overmax-probe/pointer-original-sector-003000.bin' \
  '509684004b74f7ea71c5572623494f57a95231664e06aac497f43abebbd72cc6' 'build/kw520-overmax-probe/overmax-pointer-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/overmax-pointer-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-overmax-probe/overmax-pointer-restore.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact overmax title pointer restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original title pointer already present; no write" "$log"; then
  echo "Overmax pointer-restore acceptance line missing" >&2
  exit 1
fi
