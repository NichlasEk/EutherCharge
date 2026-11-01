#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-listed-language9" ]] || { echo "Refusing: pass --restore-listed-language9" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_language_list_gate.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-language-list-gate --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-language-list-gate/language9-list-restore.cfg --mode language9-list-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/language9_list_restore.bin >/dev/null
printf '%s  %s\n' \
  'a179007a5fe525b28a8c518babd216d39eb81d4fd093688a98f5acb2baa6f6fc' 'build/kw520-spi-patch/language9_list_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-language-list-gate/original-sector-003000.bin' \
  '73a6fb8865cc8c77e32e79f3279625e333346119c9b6ea25d1f0621ac94cbb39' 'build/kw520-language-list-gate/language9-list-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/language9-list-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-language-list-gate/language9-list-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact original sector restored after language-list probe|exact original language sector already present; no write)" "$log"
