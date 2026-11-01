#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--install-stack-exec-data" ]] || { echo "Refusing: pass --install-stack-exec-data" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
make -C tools/kw520_stack_exec_probe all >/dev/null
python tools/prepare_kw520_stack_exec_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-exec-probe/stub.bin build/kw520-stack-exec-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-exec-probe/stack-exec-data-install.cfg --mode stack-exec-data-install --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/stack_exec_data_install.bin >/dev/null
printf '%s  %s\n' 'ee09624fce2ad0ec7fbfc3d8e086ec281f196669ce4916605b15ba0b85c7e5fe' 'build/kw520-spi-patch/stack_exec_data_install.bin' \
  'b579b4721aaad64d84e0c7a790d1502e9b01f5b84f732c1733950e417ed0185b' 'build/kw520-stack-exec-probe/exec-data-test-sector-00c000.bin' \
  '228e6758fb00a874039f6e17925a90e3ea3694591756527a145e4509143281cc' 'build/kw520-stack-exec-probe/stack-exec-data-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/stack-exec-data-install-session.log
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts -f build/kw520-stack-exec-probe/stack-exec-data-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (exact SRAM-marker data sector installed|exact SRAM-marker data sector already present; no write)" "$log"
