#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-stack-exec-data" ]] || { echo "Refusing: pass --restore-stack-exec-data" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
make -C tools/kw520_stack_exec_probe all >/dev/null
python tools/prepare_kw520_stack_exec_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-exec-probe/stub.bin build/kw520-stack-exec-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-exec-probe/stack-exec-data-restore.cfg --mode stack-exec-data-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/stack_exec_data_restore.bin >/dev/null
printf '%s  %s\n' 'e4de4bb06c61d0cb23cb35bf1a1419b696acaa01544ae3f1cd2eec026d3ce717' 'build/kw520-spi-patch/stack_exec_data_restore.bin' \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-stack-exec-probe/data-original-sector-00c000.bin' \
  '95c8a7d92f66e6d9a04f278d880e27615a2d0f721b3789c0e0d0943bd52ad4c5' 'build/kw520-stack-exec-probe/stack-exec-data-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/stack-exec-data-restore-session.log
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts -f build/kw520-stack-exec-probe/stack-exec-data-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (SRAM-marker data sector restored to exact all-FF|SRAM-marker data sector already exact all-FF; no write)" "$log"
