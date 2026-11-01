#!/bin/bash
set -euo pipefail
[[ ${1:-} == "--allocation" && ${2:-} =~ ^(256|320|384|448|480|512)$ && ${3:-} == "--write-data" && ( -z ${4:-} || ${4:-} == "--verify-only" ) ]] || {
  echo "Usage: $0 --allocation <256|320|384|448|480|512> --write-data [--verify-only]" >&2; exit 2;
}
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd); cd "$repo_dir"
allocation=$2
case $allocation in
  256) helper_hash=2b283d0f8a616e65f35ae306c0b089f3e69e6732d26939d8bc2feb96728195ea; sector_hash=8e24beb9d748611fea4c191ac5de47d21ce874de14ec0d20c282d40602d0e7b8; cfg_hash=ec7b73806e7ab2549c1442493d37f3cd156b0e914e5088d691817c3dbbadce83 ;;
  320) helper_hash=5d1a31b182789fbcea4d5f495ae4ed3e3a2bd0bf455c7eb62030b5d1962115d6; sector_hash=0f04c18e02b90755014db47fd0a7dfd9f6fdee599b0ebd0c6d673af6e51a852a; cfg_hash=71ccbe93eb55f245a04af951e60aef17e78482eaaaae9be6fb6c2795cbff628c ;;
  384) helper_hash=7ec88b33aecdec3325fabaf31e5e2e5f2e84c9420f4dc58ef87a47bccd292005; sector_hash=41d3bdb3cc6e6ce5cad9d9b04ac371dfca53380a3701d2d69a645cf05decbb62; cfg_hash=39686aad9550d757be5750432b20931965c87e79d6ec0dd9c484bca1aaba8443 ;;
  448) helper_hash=efb303f48bd8ab53411e235414ee49ded0dc443a7d99e8c2ec50e993f99165c9; sector_hash=e332c967d0097bacfa4cbd62e726b96772b3ee0e4b19972f5699dffc947f9f82; cfg_hash=ef1a5ee62b0c520b8b0060dccf8faf00293bf8bfee8779c5cf8eccfe8e705df0 ;;
  480) helper_hash=d134ddd9394f0239f9830e414261abc3356fe7a0f5fd71eec56000f4bb0d97a8; sector_hash=ed7e236286070c3e3addf21b2fc156de21337c375e9b449d712f823d5a3cbe2c; cfg_hash=502e96e61c93091edb529a273533e19e03203ab3a7007f4cd411ef3fe98c5c3e ;;
  512) helper_hash=cfebd7ea1e3ca4f6b1fe8a5ee16688fa7058feac0a2bd16946f24f5bf6a6dcd2; sector_hash=505883a649f7d8bbb679c18a0bd315b47f4c273f431e9800ec1368804747b8e8; cfg_hash=616f280d111e4b6a5875b408c595c30684df064d15da59342c05b2481b973b20 ;;
esac
python tools/prepare_kw520_stack_frontier.py dumps/readback/kw520-after-euthercharge-2026-10-18.bin build/kw520-stack-frontier --force >/dev/null
make -C tools/kw520_spi_patch "../../build/kw520-spi-patch/frontier${allocation}_data_install.bin" >/dev/null
python tools/prepare_kw520_overmax_openocd.py tools/kw520_spi_patch/restore-noop.cfg "build/kw520-stack-frontier/frontier${allocation}-data-install.cfg" --mode "frontier${allocation}-data-install" --force
printf '%s  %s\n' \
  "$helper_hash" "build/kw520-spi-patch/frontier${allocation}_data_install.bin" \
  "$sector_hash" "build/kw520-stack-frontier/alloc-${allocation}-data-test-sector-00c000.bin" \
  "$cfg_hash" "build/kw520-stack-frontier/frontier${allocation}-data-install.cfg" | sha256sum -c -
[[ ${4:-} != "--verify-only" ]] || exit 0
log="build/kw520-stack-frontier/frontier${allocation}-data-install-session.log"
[[ ! -e $log ]] || { echo "Refusing to replace $log" >&2; exit 2; }
build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/bin/openocd \
  -s build/toolchains/idf-tools/tools/openocd-esp32/v0.12.0-esp32-20250707/openocd-esp32/share/openocd/scripts \
  -f "build/kw520-stack-frontier/frontier${allocation}-data-install.cfg" 2>&1 | tee "$log"
grep -Eq "ACCEPTED: cyclic allocation-${allocation} data sector (installed and verified|already present; no write)" "$log"
