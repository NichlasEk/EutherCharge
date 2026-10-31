#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-crossbank-probe" ]]; then
  echo "Refusing: pass --write-crossbank-probe for Huvudmeny -> French Menu principal" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_crossbank_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-crossbank-probe --force >/dev/null
python tools/prepare_kw520_crossbank_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-crossbank-probe/crossbank-probe.cfg --mode probe --force
python tools/prepare_kw520_crossbank_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-crossbank-probe/crossbank-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '75d9cf3a479d35aacbcbec46bb8a46b43e3900fe354446150892bc3a7218811a' 'build/kw520-spi-patch/crossbank_probe.bin' \
  'c2efac5633809ad1347cbe01e554d8b15789e21aeb18796b7770875e95982842' 'build/kw520-spi-patch/crossbank_restore.bin' \
  '3efd9a22de5e71a4e864cb712058c21180eb660eedeba50718969b506559c72d' 'build/kw520-crossbank-probe/crossbank-sector-003000.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-crossbank-probe/restore-sector-003000.bin' \
  '49c4868b44238fbb70e33383439523fdb4c6a9f4106ad78dfc597a31672069e8' 'build/kw520-crossbank-probe/crossbank-probe.cfg' \
  '170ee88061acc3344ec45fd00b51ec9e711d7ac55d273c61655965e368dc0d1e' 'build/kw520-crossbank-probe/crossbank-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/crossbank-probe-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-crossbank-probe/crossbank-probe.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact cross-bank pointer probe programmed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact cross-bank sector already present; no write" "$log"; then
  echo "Cross-bank probe acceptance line missing; target state is not accepted" >&2
  exit 1
fi
