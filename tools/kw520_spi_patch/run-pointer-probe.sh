#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-pointer-probe" ]]; then
  echo "Refusing: pass --write-pointer-probe for the fixed Huvudmeny -> Testa pointer experiment" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_pointer_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-pointer-probe --force >/dev/null
python tools/prepare_kw520_pointer_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-pointer-probe/pointer-probe.cfg --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '26bf5766a54891df9716b25b7771a512bc6a3c98105adc603b40dfa232c36a79' 'build/kw520-spi-patch/pointer_probe.bin' \
  '9b2df2c5e404b2a6c258869af7496f83ca086dc45d2be080d2ea07352ddfe744' 'build/kw520-spi-patch/pointer_restore.bin' \
  'e2a360307ecdf51373df959d68b3b8446aba39fc7aa69d7da863c3d4e52a0028' 'build/kw520-pointer-probe/pointer-sector-003000.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-pointer-probe/restore-sector-003000.bin' \
  'eed75c35fce464dbcd07f2923794fee12bf9bcf3dfa9ae9346c972a3a62b8725' 'build/kw520-pointer-probe/pointer-probe.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/pointer-probe-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-pointer-probe/pointer-probe.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact same-bank pointer probe programmed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact pointer-probe sector already present; no write" "$log"; then
  echo "Pointer-probe acceptance line missing; target state is not accepted" >&2
  exit 1
fi
