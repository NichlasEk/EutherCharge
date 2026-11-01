#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary128-pointer" ]]; then
  echo "Refusing: pass --write-boundary128-pointer to point only the title to record 0x00c000" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary128_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary128-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary128-probe/boundary128-pointer-install.cfg --mode boundary128-pointer-install --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  'ac3a3c8159b8512acda2f6114c86dd06bb425f0a52ea1fea3c10e82be2ce1715' 'build/kw520-spi-patch/overmax_pointer_install.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-boundary128-probe/pointer-test-sector-003000.bin' \
  '33b9e83b43b13c740c6673d874ee2555f0ea8c015f01a9fbfcedbd57a145cef5' 'build/kw520-boundary128-probe/boundary128-pointer-install.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary128-pointer-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary128-probe/boundary128-pointer-install.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: exact allocation-128 title pointer installed and verified" "$log" && \
   ! grep -Fq "ACCEPTED: exact allocation-128 title pointer already present; no write" "$log"; then
  echo "Allocation-128 pointer-install acceptance line missing" >&2
  exit 1
fi
