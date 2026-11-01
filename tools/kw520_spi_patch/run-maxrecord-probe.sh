#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-maxrecord-probe" ]]; then
  echo "Refusing: pass --write-maxrecord-probe to point the title to the existing 113-byte record" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_maxrecord_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-maxrecord-probe --force >/dev/null
python tools/prepare_kw520_maxrecord_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-maxrecord-probe/maxrecord-probe.cfg --mode probe --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '50b0d18ee1783269fc9ff116a002f9df20edd3f25d27882b58979b15039f9a8a' 'build/kw520-spi-patch/maxrecord_probe.bin' \
  '856efe786f0a46c3d812229146046ce28cfaed436ccfc2e776768772f0333707' 'build/kw520-maxrecord-probe/maxrecord-sector-003000.bin' \
  '4e2656b13627670549be9b1863df444fae997c0ceb257cb2b6373ad14e7eb2b0' 'build/kw520-maxrecord-probe/maxrecord-probe.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/maxrecord-probe-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-maxrecord-probe/maxrecord-probe.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact maximum-record pointer probe programmed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact maximum-record pointer sector already present; no write" "$log"; then
  echo "Maximum-record probe acceptance line missing" >&2
  exit 1
fi
