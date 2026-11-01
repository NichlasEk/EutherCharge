#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--allocation" && ${2:-} =~ ^(256|320|384|448|480|512)$ && ${3:-} == "--restore-frontier-pointer" && ( -z ${4:-} || ${4:-} == "--verify-only" ) ]] || {
  echo "Usage: $0 --allocation <256|320|384|448|480|512> --restore-frontier-pointer [--verify-only]" >&2; exit 2;
}
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
allocation=$2
python tools/prepare_kw520_stack_frontier.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-frontier --force >/dev/null
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/frontier_pointer_bitbang_restore.bin >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-frontier/frontier-pointer-bitbang-restore.cfg --mode frontier-pointer-bitbang-restore --force
printf '%s  %s\n' \
  '521d730188404bc2140a9abcd18b9db5381e5e7a6180c1a2575f49d1bcd8b86e' 'build/kw520-spi-patch/frontier_pointer_bitbang_restore.bin' \
  '95cb89b4c6cf9a72037189adaf4d62d8050f584b784ea7f233335fce218e1ca9' 'build/kw520-stack-frontier/pointer-original-sector-003000.bin' \
  '904cfb21826c760fbabb772aee5de433b06cb0107522bddb6c70acfeecf5bdd5' 'build/kw520-stack-frontier/frontier-pointer-bitbang-restore.cfg' | sha256sum -c -
[[ ${4:-} != "--verify-only" ]] || exit 0
log="build/kw520-stack-frontier/frontier${allocation}-pointer-bitbang-restore-session.log"
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-stack-frontier/frontier-pointer-bitbang-restore.cfg 2>&1 | tee "$log"
grep -Eq 'ACCEPTED: (stack-frontier title pointer restored through bitbang SPI|original title pointer already present; bitbang helper made no write)' "$log"
