#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-nulcopy-data" ]] || { echo "Refusing: pass --restore-nulcopy-data" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_nulcopy_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-nulcopy-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-nulcopy-probe/nulcopy-data-restore.cfg --mode nulcopy-data-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/nulcopy_data_restore.bin >/dev/null
printf '%s  %s\n' \
  '877dda2da8ca715a956396ea30868dc0091527bc010194d33f6b1a47fc8af36c' 'build/kw520-spi-patch/nulcopy_data_restore.bin' \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-nulcopy-probe/data-original-sector-00c000.bin' \
  '754846b704ad56bdc6d6b7f934648684f6b61ef29e4f9f11fceee74d22832e76' 'build/kw520-nulcopy-probe/nulcopy-data-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/nulcopy-data-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-nulcopy-probe/nulcopy-data-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (embedded-NUL data sector restored to exact all-FF|embedded-NUL data sector already exact all-FF; no write)" "$log"
