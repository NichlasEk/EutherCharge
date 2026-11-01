#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--write-boundary224-pointer" ]] || { echo "Refusing: pass --write-boundary224-pointer" >&2; exit 2; }
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
python tools/prepare_kw520_boundary_transition.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary224-probe --from-allocation 192 --to-allocation 224 --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary224-probe/boundary224-pointer-install-retry.cfg --mode boundary224-pointer-install-retry --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '1c08ec765fccaf3925dcd1702af14bd37a6ad48e58041f3b9b27cb8ede77d4ff' 'build/kw520-spi-patch/boundary_pointer_install_retry.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-boundary224-probe/pointer-test-sector-003000.bin' \
  '35b483ccd6bf7c614e7491728214176fde89e2b410fda5566170a7c4892afb3a' 'build/kw520-boundary224-probe/boundary224-pointer-install-retry.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary224-pointer-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary224-probe/boundary224-pointer-install-retry.cfg 2>&1 | tee "$log"
grep -Eq "ACCEPTED: (allocation-224 title pointer installed with bounded status retry|allocation-224 title pointer already present; bounded helper made no write)" "$log"
