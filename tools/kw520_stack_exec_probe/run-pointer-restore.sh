#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--restore-stack-exec-pointer" ]] || { echo "Refusing: pass --restore-stack-exec-pointer" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
make -C tools/kw520_stack_exec_probe all >/dev/null
python tools/prepare_kw520_stack_exec_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-exec-probe/stub.bin build/kw520-stack-exec-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-exec-probe/stack-exec-pointer-bitbang-restore.cfg --mode stack-exec-pointer-bitbang-restore --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/frontier_pointer_bitbang_restore.bin >/dev/null
printf '%s  %s\n' '521d730188404bc2140a9abcd18b9db5381e5e7a6180c1a2575f49d1bcd8b86e' 'build/kw520-spi-patch/frontier_pointer_bitbang_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-stack-exec-probe/pointer-original-sector-003000.bin' \
  'ada54402eddd9aae48b90b69e4796f626c6912a93896205428319e7b0e696b45' 'build/kw520-stack-exec-probe/stack-exec-pointer-bitbang-restore.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/stack-exec-pointer-restore-session.log
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts -f build/kw520-stack-exec-probe/stack-exec-pointer-bitbang-restore.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (SRAM-marker title pointer restored through bitbang SPI|original title pointer already present; bitbang helper made no write)" "$log"
