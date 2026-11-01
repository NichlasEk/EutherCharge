#!/bin/bash
set -euo pipefail

[[ ${1:-} == "--candidate-18-sram-copy" && ${2:-} =~ ^[a-z0-9][a-z0-9-]{0,47}$ && -z ${3:-} ]] || {
  echo "Usage: $0 --candidate-18-sram-copy <lowercase-label>" >&2
  exit 2
}

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
label=$2
out="build/kw520-call-oracle/$label"
[[ ! -e $out ]] || { echo "Refusing to replace $out" >&2; exit 2; }
mkdir -p "$out"

make -C tools/kw520_call_oracle all >/dev/null
oracle_hash=9fb2cb3c8459fdee2980da1d552d1de470dc371e5a7f1c4c03dc6956d097d1a4
printf '%s  %s\n' "$oracle_hash" build/kw520-call-oracle/oracle.bin | sha256sum -c -

export KW520_ORACLE_OUT_DIR=$out
openocd=build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd
scripts=build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts
set +e
"$openocd" -s "$scripts" -f tools/kw520_call_oracle/candidate18.cfg 2>&1 | tee "$out/session.log"
openocd_status=${PIPESTATUS[0]}
set -e

grep -Eq "ORACLE_OUTCOME (exact-copy|returned-mismatch|contained-fault|contained-timeout)" "$out/session.log"
grep -Eq "ORACLE_CANDIDATE .*index=18 candidate=0800ad8f .*address_ok=1" "$out/session.log"
grep -Fq "RESTORED_VTOR=0x08000000" "$out/session.log"
cmp -s build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin"
cmp -s "$out/sram-backup.bin" "$out/sram-restored.bin"
sha256sum build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin" \
  "$out/sram-backup.bin" "$out/sram-restored.bin" "$out/oracle-data.bin"
echo "OPENOCD_STATUS=$openocd_status"
echo "ACCEPTED: candidate 18 was contained and all affected SRAM was restored"
