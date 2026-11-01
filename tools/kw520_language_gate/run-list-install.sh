#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--install-listed-language9" ]] || { echo "Refusing: pass --install-listed-language9" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_language_list_gate.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-language-list-gate --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-language-list-gate/language9-list-install.cfg --mode language9-list-install --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/language9_list_install.bin >/dev/null
printf '%s  %s\n' \
  '73d2a00ff65d72e9804492816c63ec8fbe10403455a01405f1d8457f1dd2f450' 'build/kw520-spi-patch/language9_list_install.bin' \
  '3fc0b1c28a4902a4a486d558dc6f764d6aa179bd4cb487383074990444818404' 'build/kw520-language-list-gate/language9-listed-test-sector-003000.bin' \
  '2fa7d6a95f456a992d16aa25fc4fc44cbee6641d51b253e2d47a2644781cc699' 'build/kw520-language-list-gate/language9-list-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/language9-list-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-language-list-gate/language9-list-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact consistent language-9 list sector installed|exact consistent language-9 list sector already present; no write)" "$log"
