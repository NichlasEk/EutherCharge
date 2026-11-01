#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--activate-stack-exec-pointer" ]] || { echo "Refusing: pass --activate-stack-exec-pointer" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
make -C tools/kw520_stack_exec_probe all >/dev/null
python tools/prepare_kw520_stack_exec_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-exec-probe/stub.bin build/kw520-stack-exec-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-exec-probe/stack-exec-pointer-install.cfg --mode stack-exec-pointer-install --force
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary_pointer_install_retry.bin >/dev/null
printf '%s  %s\n' '1c08ec765fccaf3925dcd1702af14bd37a6ad48e58041f3b9b27cb8ede77d4ff' 'build/kw520-spi-patch/boundary_pointer_install_retry.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-stack-exec-probe/pointer-test-sector-003000.bin' \
  'e0e78f25322af20826b6bfb0a8d31bab747e829a1979eb41f40d4b5a9b1c7e21' 'build/kw520-stack-exec-probe/stack-exec-pointer-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/stack-exec-pointer-install-session.log
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts -f build/kw520-stack-exec-probe/stack-exec-pointer-install.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (SRAM-marker title pointer installed and verified|SRAM-marker title pointer already present; no write)" "$log"
