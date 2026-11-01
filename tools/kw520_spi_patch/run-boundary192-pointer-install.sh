#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary192-pointer" ]]; then
  echo "Refusing: pass --write-boundary192-pointer for bounded pointer activation" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary192-probe --from-allocation 160 --to-allocation 192 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary192-probe/boundary192-pointer-install-retry.cfg --mode boundary192-pointer-install-retry --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '1c08ec765fccaf3925dcd1702af14bd37a6ad48e58041f3b9b27cb8ede77d4ff' 'build/kw520-spi-patch/boundary_pointer_install_retry.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-boundary192-probe/pointer-test-sector-003000.bin' \
  'b5e7ea572c2235cba5671aa9cbfb3c1c4a2e8dbfc0d456c56e56f2cc9c7cd680' 'build/kw520-boundary192-probe/boundary192-pointer-install-retry.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary192-pointer-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary192-probe/boundary192-pointer-install-retry.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (allocation-192 title pointer installed with bounded status retry|allocation-192 title pointer already present; bounded helper made no write)" "$log"
