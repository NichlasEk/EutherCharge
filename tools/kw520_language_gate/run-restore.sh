#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-language8" ]] || { echo "Refusing: pass --restore-language8" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_language_gate.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-language-gate --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-language-gate/language9-restore.cfg --mode language9-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/language9_restore.bin >/dev/null
printf '%s  %s\n' \
  '3b4577e7187f2aecd86314ea09cfeece107657b7e2fce6b0f9cdd686d9baf3f9' 'build/kw520-spi-patch/language9_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-language-gate/original-sector-003000.bin' \
  '515170a607e6bd99f3a22784ea72fe577ecf2502a1592b73c9f5f01f0e7046bc' 'build/kw520-language-gate/language9-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/language9-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-language-gate/language9-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact original 8-language directory sector restored|exact original 8-language directory sector already present; no write)" "$log"
