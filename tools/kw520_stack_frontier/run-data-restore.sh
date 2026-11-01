#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--allocation" && ${2:-} =~ ^(256|320|384|448|480|512)$ && ${3:-} == "--restore-data" && ( -z ${4:-} || ${4:-} == "--verify-only" ) ]] || {
  echo "Usage: $0 --allocation <256|320|384|448|480|512> --restore-data [--verify-only]" >&2; exit 2;
}
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
allocation=$2
case $allocation in
  256) helper_hash=5e70fe2da2d63889db5543ea5c96a7e01eefc17204fa85d9f7f9b5f0681e02e4; cfg_hash=777a77b6250e4a817d5317c82b22d0ac57529b267328288f350541d75dec35e1 ;;
  320) helper_hash=074c59cf5ec10e075ee9f3b6e2ff470724909194f0a1718a74f68acd95fe13ec; cfg_hash=c9fc06dd4c28a718ecad562fc5318b0d74288e3d9bbe15584fcede1e536562bf ;;
  384) helper_hash=a39bcee97a5c6a189090e19014a8ed3783245588c3fb605705cb34dc58e2b7b9; cfg_hash=44edda2ec0f5a478b7f010038d7cd8a927e2bd06e3344ce812b85b672fdb845b ;;
  448) helper_hash=89285c76aa6ddde7c55f1456bb8da6aea453bad2d7c46520634de5399f7c70db; cfg_hash=6dd8027e6cb8bb91e9f87d58ff9bd5bd5c9b27459829cb548b92cd78e67764f1 ;;
  480) helper_hash=0f5ade065f18f809991124b683b6bf0a596b0b64de9c81cd6ed2ed55bde7665b; cfg_hash=d6d3602bdaa682ad05b7a86e61d0b9892c526f45a500be40aaeb5ca5e0c8d1be ;;
  512) helper_hash=5a0c6535e0f72fe3b2b4e79f570488a855211cec09696748b1134afa6d966f22; cfg_hash=41c7b850326d12ff98d61a365b34540cd1fa026d28fcdaca4631f3061bc8e2ae ;;
esac
python tools/prepare_kw520_stack_frontier.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-frontier --force >/dev/null
make -C tools/kw520_spi_patch "../../build/kw520-spi-patch/frontier${allocation}_data_restore.bin" >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg "build/kw520-stack-frontier/frontier${allocation}-data-restore.cfg" --mode "frontier${allocation}-data-restore" --force
printf '%s  %s\n' \
  "$helper_hash" "build/kw520-spi-patch/frontier${allocation}_data_restore.bin" \
  'f47a8ec3e9aff2318d896942282ad4fe37d6391c82914f54a5da8a37de1300c6' 'build/kw520-stack-frontier/data-original-sector-00c000.bin' \
  "$cfg_hash" "build/kw520-stack-frontier/frontier${allocation}-data-restore.cfg" | sha256sum -c -
[[ ${4:-} != "--verify-only" ]] || exit 0
log="build/kw520-stack-frontier/frontier${allocation}-data-restore-session.log"
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f "build/kw520-stack-frontier/frontier${allocation}-data-restore.cfg" 2>&1 | tee "$log"
grep -Eq "ACCEPTED: allocation-${allocation} data sector (restored to exact all-FF|already exact all-FF; no write)" "$log"
