#!/bin/bash
set -euo pipefail

if [[ ${1:-} != "--capture" || ! ${2:-} =~ ^(256|320|384|448|480|512)$ || ! ${3:-} =~ ^[a-z0-9][a-z0-9-]{0,47}$ ]]; then
  echo "Usage: $0 --capture <256|320|384|448|480|512> <lowercase-label>" >&2
  exit 2
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
allocation=$2
label=$3
base="build/kw520-stack-frontier/captures/$label"
sram="$base.bin"
log="$base.log"
report="$base.json"
for output in "$sram" "$log" "$report"; do
  [[ ! -e $output ]] || { echo "Refusing to replace $output" >&2; exit 2; }
done
mkdir -p build/kw520-stack-frontier/captures
export KW520_FRONTIER_SRAM_OUTPUT=$sram

build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f tools/kw520_stack_frontier/capture.cfg 2>&1 | tee "$log"
grep -Fq "FRONTIER_CAPTURE=PASS" "$log"
[[ $(stat -c %s "$sram") == 16384 ]]
python tools/kw520_stack_frontier/analyze_capture.py \
  --allocation "$allocation" --sram "$sram" --log "$log" --output "$report"
sha256sum "$sram" "$report"
