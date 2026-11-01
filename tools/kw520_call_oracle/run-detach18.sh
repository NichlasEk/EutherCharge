#!/bin/bash
set -euo pipefail

[[ ${1:-} == "--detach-candidate-18-sram-copy" && ${2:-} =~ ^[a-z0-9][a-z0-9-]{0,47}$ && -z ${3:-} ]] || {
  echo "Usage: $0 --detach-candidate-18-sram-copy <lowercase-label>" >&2
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
"$openocd" -s "$scripts" -f tools/kw520_call_oracle/detach-arm.cfg 2>&1 | tee "$out/arm.log"
arm_status=${PIPESTATUS[0]}
set -e
arm_gate=0
if grep -Fq "ACCEPTED: candidate 18 is waiting for debug detach" "$out/arm.log" \
  && grep -Eq "DETACH_ARM .*state=00000040 command=3 index=18 candidate=0800ad8f arm_ok=1" "$out/arm.log" \
  && grep -Fq "DETACH_RELEASE status=0xc0000040" "$out/arm.log" \
  && cmp -s build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin"; then
  arm_gate=1
fi
[[ -f $out/sram-backup.bin ]] || { echo "No SRAM backup exists; phase 1 stopped before target load" >&2; exit 3; }

# The helper itself waits for C_DEBUGEN=0; this short host interval only gives
# the detached candidate time to return or enter the contained fault path.
sleep 1

set +e
"$openocd" -s "$scripts" -f tools/kw520_call_oracle/detach-readback.cfg 2>&1 | tee "$out/readback.log"
readback_status=${PIPESTATUS[0]}
set -e
grep -Eq "DETACH_OUTCOME (exact-copy|returned-mismatch|contained-fault|no-return-after-branch|debug-never-detached)" "$out/readback.log"
grep -Eq "DETACH_RESULT .*index=18 candidate=0800ad8f .*address_ok=1" "$out/readback.log"
grep -Fq "RESTORED_VTOR=0x08000000" "$out/readback.log"
cmp -s "$out/sram-backup.bin" "$out/sram-restored.bin"
[[ $arm_gate == 1 ]]
sha256sum build/kw520-call-oracle/oracle.bin "$out/oracle-readback.bin" \
  "$out/sram-backup.bin" "$out/sram-restored.bin" "$out/oracle-data.bin"
echo "ARM_OPENOCD_STATUS=$arm_status READBACK_OPENOCD_STATUS=$readback_status"
echo "ACCEPTED: detached candidate 18 was observed and all affected SRAM was restored"
