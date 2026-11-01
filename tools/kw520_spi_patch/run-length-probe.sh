#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-length-probe" ]]; then
  echo "Refusing: pass --write-length-probe to shorten main-title length 10 -> 8" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_length_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-length-probe --force >/dev/null
python tools/prepare_kw520_length_openocd.py \
  tools/kw520_spi_patch/format-probe.cfg \
  build/kw520-length-probe/length-probe.cfg --mode probe --force
python tools/prepare_kw520_length_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-length-probe/length-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  'c2807513f45fe679357bb2582eeb41e0191548413dee0da05ae911b7a6e3fd1b' 'build/kw520-spi-patch/length_probe.bin' \
  '56e96f438c652c1053a753e9223e18f05c92dbdd2f3f7e75fa10381e526c330b' 'build/kw520-spi-patch/length_restore.bin' \
  'aab42735188c7827a8d8ede1769430384ded21d0fd2948ac8ec28707228e5c28' 'build/kw520-length-probe/length-sector-003000.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-length-probe/restore-sector-003000.bin' \
  '03b9f520e58a69c4eb64badd565ceb3183aa2a312d4ba23b59e33d861e0ad969' 'build/kw520-length-probe/length-probe.cfg' \
  'cf5e004c174fe1114abee1f0c9eaaa6d5314be81bdabd88b1878735b24421148' 'build/kw520-length-probe/length-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/length-probe-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-length-probe/length-probe.cfg \
  2>&1 | tee "$log"

grep -Fq "ACCEPTED: exact declared-length shortening programmed and verified" "$log" || {
  echo "Length-probe acceptance line missing; target state is not accepted" >&2
  exit 1
}
