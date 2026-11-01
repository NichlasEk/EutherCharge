#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--restore-boundary-probe" ]]; then
  echo "Refusing: pass --restore-boundary-probe to accept only fixed baseline, extension, or original" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

python tools/prepare_kw520_boundary_probe.py \
  dumps/readback/kw520-after-euthercharge-2026-10-18.bin \
  build/kw520-boundary-probe --force >/dev/null
python tools/prepare_kw520_boundary_openocd.py \
  tools/kw520_spi_patch/restore-noop.cfg \
  build/kw520-boundary-probe/boundary-restore.cfg --mode restore --force
make -C tools/kw520_spi_patch all >/dev/null

printf '%s  %s\n' \
  '709972902923197981493c5562b84aa6f2ed7bc43637931f37d69ec2f1ee7235' 'build/kw520-spi-patch/boundary_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-boundary-probe/original-sector-003000.bin' \
  'cd82f6596c56fed1905638299fb5afd06296a6eb445e37d75da94cf8a43cc42a' 'build/kw520-boundary-probe/boundary-restore.cfg' | sha256sum -c -

log=build/kw520-jlink-20261031/boundary-restore-session.log
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-boundary-probe/boundary-restore.cfg \
  2>&1 | tee "$log"

if ! grep -Fq "ACCEPTED: exact boundary-test sector restored and verified" "$log" && \
   ! grep -Fq "ACCEPTED: original sector already present; no boundary restore write" "$log"; then
  echo "Boundary-restore acceptance line missing; target state is not accepted" >&2
  exit 1
fi
