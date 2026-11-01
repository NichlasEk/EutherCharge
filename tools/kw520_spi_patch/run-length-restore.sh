#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-length-probe" ]]; then
  echo "Refusing: pass --restore-length-probe to restore only sector CRC 5e1e3b15" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_length_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-length-probe --force >/dev/null
python tools/prepare_kw520_length_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-length-probe/length-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '56e96f438c652c1053a753e9223e18f05c92dbdd2f3f7e75fa10381e526c330b' 'build/kw520-spi-patch/length_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-length-probe/restore-sector-003000.bin' \
  'cf5e004c174fe1114abee1f0c9eaaa6d5314be81bdabd88b1878735b24421148' 'build/kw520-length-probe/length-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/length-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-length-probe/length-restore.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact declared-length sector restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original sector already present; no length restore write" "$log"; then
  echo "Length-restore acceptance line missing; target state is not accepted" >&2
  exit 1
fi
