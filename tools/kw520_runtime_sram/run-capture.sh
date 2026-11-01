#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--capture" || ! ${2:-} =~ ^[a-z0-9][a-z0-9-]{0,47}$ ]]; then
  echo "Usage: $0 --capture <lowercase-label>" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"

output="build/kw520-runtime-sram/$2.bin"
log="build/kw520-runtime-sram/$2.log"
if [[ -e $output || -e $log ]]; then
  echo "Refusing to replace existing capture or log for label: $2" >&2
  exit 2
fi
mkdir -p build/kw520-runtime-sram
export KW520_RUNTIME_SRAM_OUTPUT=$output

build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f tools/kw520_runtime_sram/capture.cfg \
  2>&1 | tee "$log"

grep -Fq "RUNTIME_SRAM_CAPTURE=PASS" "$log" || {
  echo "SRAM capture acceptance line missing" >&2
  exit 1
}
size=$(stat -c %s "$output")
if [[ $size != 16384 ]]; then
  echo "SRAM capture has size $size, expected 16384" >&2
  exit 1
fi
sha256sum "$output"
