#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-pointer-probe" ]]; then
  echo "Refusing: pass --restore-pointer-probe to restore only pointer-sector CRC 14b0524b" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_pointer_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-pointer-probe --force >/dev/null
python tools/prepare_kw520_pointer_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-pointer-probe/pointer-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '9b2df2c5e404b2a6c258869af7496f83ca086dc45d2be080d2ea07352ddfe744' 'build/kw520-spi-patch/pointer_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-pointer-probe/restore-sector-003000.bin' \
  'b3cf904feab3feb5ee258ab637aa09fa22055e9f1306c4e40cacd4263110d29f' 'build/kw520-pointer-probe/pointer-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/pointer-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-pointer-probe/pointer-restore.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact pointer-probe sector restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original sector already present; no pointer restore write" "$log"; then
  echo "Pointer-restore acceptance line missing; target state is not accepted" >&2
  exit 1
fi
