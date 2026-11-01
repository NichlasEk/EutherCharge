#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--write-boundary160-pointer" ]]; then
  echo "Refusing: pass --write-boundary160-pointer for the bounded pointer activation" >&2
  exit 2
fi
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
python tools/prepare_kw520_boundary160_probe.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-boundary160-probe --force >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-boundary160-probe/boundary160-pointer-install-retry.cfg --mode boundary160-pointer-install-retry --force
make -C tools/kw520_spi_patch all >/dev/null
printf '%s  %s\n' \
  '1c08ec765fccaf3925dcd1702af14bd37a6ad48e58041f3b9b27cb8ede77d4ff' 'build/kw520-spi-patch/boundary_pointer_install_retry.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-boundary160-probe/pointer-test-sector-003000.bin' \
  '6bcefd74b7b1ea8a1cc87b20d059fadb5db4a093245d8af90cce864f3c78060d' 'build/kw520-boundary160-probe/boundary160-pointer-install-retry.cfg' | sha256sum -c -
log=build/kw520-jlink-20261031/boundary160-pointer-install-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary160-probe/boundary160-pointer-install-retry.cfg 2>&1 | tee "$log"
if ! grep -Fq "ACCEPTED: allocation-160 title pointer installed with bounded status retry" "$log" && \
   ! grep -Fq "ACCEPTED: allocation-160 title pointer already present; bounded helper made no write" "$log"; then
  echo "Allocation-160 pointer-install acceptance line missing" >&2
  exit 1
fi
