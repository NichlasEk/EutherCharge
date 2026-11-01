#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--allocation" && ${2:-} =~ ^(256|320|384|448|480|512)$ && ${3:-} == "--activate-frontier-pointer" && ( -z ${4:-} || ${4:-} == "--verify-only" ) ]] || {
  echo "Usage: $0 --allocation <256|320|384|448|480|512> --activate-frontier-pointer [--verify-only]" >&2; exit 2;
}
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
allocation=$2
python tools/prepare_kw520_stack_frontier.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-frontier --force >/dev/null
make -C tools/kw520_spi_patch ../../build/kw520-spi-patch/boundary_pointer_install_retry.bin >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg build/kw520-stack-frontier/frontier-pointer-install.cfg --mode frontier-pointer-install --force
printf '%s  %s\n' \
  '1c08ec765fccaf3925dcd1702af14bd37a6ad48e58041f3b9b27cb8ede77d4ff' 'build/kw520-spi-patch/boundary_pointer_install_retry.bin' \
  '665aa311188576ffc9389f05f035656e12d1980007706c9dda095da2de126ba3' 'build/kw520-stack-frontier/pointer-test-sector-003000.bin' \
  'feeb804d8a9ed86c288555736ea2e91df9c6095d9127ddb76cfc2551af1a450e' 'build/kw520-stack-frontier/frontier-pointer-install.cfg' | sha256sum -c -
[[ ${4:-} != "--verify-only" ]] || exit 0
log="build/kw520-stack-frontier/frontier${allocation}-pointer-install-session.log"
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f build/kw520-stack-frontier/frontier-pointer-install.cfg 2>&1 | tee "$log"
grep -Eq 'ACCEPTED: stack-frontier title pointer (installed and verified|already present; no write)' "$log"
