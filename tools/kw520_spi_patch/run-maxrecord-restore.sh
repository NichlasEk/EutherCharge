#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-maxrecord-probe" ]]; then
  echo "Refusing: pass --restore-maxrecord-probe to accept only exact test or original sector" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_maxrecord_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-maxrecord-probe --force >/dev/null
python tools/prepare_kw520_maxrecord_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-maxrecord-probe/maxrecord-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '72ffd2a94c0030550d9fa894c3841be32eb5cc7000dd6fe21c5af65eb3e8f707' 'build/kw520-spi-patch/maxrecord_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-maxrecord-probe/original-sector-003000.bin' \
  'd8e1fe482f2c37c2497f2aa951a155f296acdb684f80a781906906d43292614c' 'build/kw520-maxrecord-probe/maxrecord-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/maxrecord-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-maxrecord-probe/maxrecord-restore.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact maximum-record pointer sector restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original sector already present; no maximum-record restore write" "$log"; then
  echo "Maximum-record restore acceptance line missing" >&2
  exit 1
fi
