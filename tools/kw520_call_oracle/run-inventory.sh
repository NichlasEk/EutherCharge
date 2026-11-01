#!/bin/bash
set -euo pipefail

[[ ${1:-} == "--inventory-only" && ${2:-} =~ ^[a-z0-9][a-z0-9-]{0,47}$ && -z ${3:-} ]] || {
  echo "Usage: $0 --inventory-only <lowercase-label>" >&2
  exit 2
}

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
label=$2
out="build/kw520-call-oracle/$label"
for path in "$out"; do
  [[ ! -e $path ]] || { echo "Refusing to replace $path" >&2; exit 2; }
done
mkdir -p "$out"

make -C tools/kw520_call_oracle all >/dev/null
oracle_hash=9fb2cb3c8459fdee2980da1d552d1de470dc371e5a7f1c4c03dc6956d097d1a4
printf '%s  %s\n' "$oracle_hash" build/kw520-call-oracle/oracle.bin | sha256sum -c -

export KW520_ORACLE_OUT_DIR=$out
openocd=build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd
scripts=build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts
set +e
"$openocd" -s "$scripts" -f tools/kw520_call_oracle/inventory.cfg 2>&1 | tee "$out/session.log"
openocd_status=${PIPESTATUS[0]}
set -e

grep -Fq "ACCEPTED: MPU inventory completed without arming a candidate" "$out/session.log"
grep -Eq "ORACLE_INVENTORY .*regions=8 .*inventory_ok=1 call_guard_ok=1" "$out/session.log"
grep -Fq "RESTORED_VTOR=0x08000000" "$out/session.log"
cmp -s build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin"
cmp -s "$out/sram-backup.bin" "$out/sram-restored.bin"
sha256sum build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin" \
  "$out/sram-backup.bin" "$out/sram-restored.bin"
echo "OPENOCD_STATUS=$openocd_status"
echo "ACCEPTED: helper readback and complete 0x1300-byte affected SRAM restoration match"
