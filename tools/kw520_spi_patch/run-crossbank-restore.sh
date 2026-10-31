#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-crossbank-probe" ]]; then
  echo "Refusing: pass --restore-crossbank-probe to restore only sector CRC b29ee7d1" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_crossbank_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-crossbank-probe --force >/dev/null
python tools/prepare_kw520_crossbank_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-crossbank-probe/crossbank-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  'c2efac5633809ad1347cbe01e554d8b15789e21aeb18796b7770875e95982842' 'build/kw520-spi-patch/crossbank_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-crossbank-probe/restore-sector-003000.bin' \
  '170ee88061acc3344ec45fd00b51ec9e711d7ac55d273c61655965e368dc0d1e' 'build/kw520-crossbank-probe/crossbank-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/crossbank-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-crossbank-probe/crossbank-restore.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact cross-bank pointer sector restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original sector already present; no cross-bank restore write" "$log"; then
  echo "Cross-bank restore acceptance line missing; target state is not accepted" >&2
  exit 1
fi
