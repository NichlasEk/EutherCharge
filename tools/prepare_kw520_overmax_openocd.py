#!/usr/bin/env python3
"""Derive four fixed OpenOCD gates for the two-sector over-maximum probe."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


TEMPLATE_SHA256 = "710926ea8b61331246bb235f1466bf8efc42e2191b2da90774f4b3db211b4704"
OLD_NOOP = "set noop_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x42 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0xf5c23372 && $erased_crc == 0 && $final_crc == 0 && $pages == 0 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0 && $cleanup == 0}]"
OLD_WRITE = "set restore_ok [expr {$core_ok && $done && $magic == 0x4b575052 && $state == 0x41 && $jedec == 0x1c3016 && $status == 0x18 && $protection == 0xff && $buffer_crc == 0xf5c23372 && $target_crc == 0x7985c2f6 && $erased_crc == 0xf154670a && $final_crc == 0xf5c23372 && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]"

VARIANTS = {
    "data-install": {
        "stem": "overmax-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "overmax_data_install", "arm": "0x41524d47", "magic": "0x4b574449",
        "label": "OVERMAX_DATA_INSTALL", "buffer": "0x6417ecbd", "target": "0xf154670a", "final": "0x6417ecbd",
        "title": "Install only the fixed allocation-114 record in unused sector 0x00c000.",
        "accepted": "ACCEPTED: exact overmax data sector installed and verified",
        "noop": "ACCEPTED: exact overmax data sector already present; no write",
        "refused": "REFUSED: fixed overmax data-install gate did not pass",
    },
    "data-restore": {
        "stem": "overmax-data-restore", "chunk": "data-original-sector-00c000-chunk",
        "binary": "overmax_data_restore", "arm": "0x41524d48", "magic": "0x4b574452",
        "label": "OVERMAX_DATA_RESTORE", "buffer": "0xf154670a", "target": "0x6417ecbd", "final": "0xf154670a",
        "title": "Restore only fixed sector 0x00c000 to exact all-FF.",
        "accepted": "ACCEPTED: exact overmax data sector restored to all-FF",
        "noop": "ACCEPTED: overmax data sector already all-FF; no write",
        "refused": "REFUSED: fixed overmax data-restore gate did not pass",
    },
    "pointer-install": {
        "stem": "overmax-pointer-install", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "overmax_pointer_install", "arm": "0x41524d49", "magic": "0x4b574f50",
        "label": "OVERMAX_POINTER_INSTALL", "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f",
        "title": "Point the main title only to the fixed record at 0x00c000.",
        "accepted": "ACCEPTED: exact overmax title pointer installed and verified",
        "noop": "ACCEPTED: exact overmax title pointer already present; no write",
        "refused": "REFUSED: fixed overmax pointer-install gate did not pass",
    },
    "pointer-restore": {
        "stem": "overmax-pointer-restore", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "overmax_pointer_restore", "arm": "0x41524d4a", "magic": "0x4b574f52",
        "label": "OVERMAX_POINTER_RESTORE", "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372",
        "title": "Restore the main-title pointer before erasing the test data sector.",
        "accepted": "ACCEPTED: exact overmax title pointer restored and verified",
        "noop": "ACCEPTED: original title pointer already present; no write",
        "refused": "REFUSED: fixed overmax pointer-restore gate did not pass",
    },
    "boundary128-data-install": {
        "stem": "boundary128-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary128_data_install", "arm": "0x41524d4b", "magic": "0x4b573849",
        "directory": "kw520-boundary128-probe", "label": "BOUNDARY128_DATA_INSTALL",
        "buffer": "0x1f18aa83", "target": "0xf154670a", "final": "0x1f18aa83",
        "title": "Install only the fixed allocation-128 record in unused sector 0x00c000.",
        "accepted": "ACCEPTED: exact allocation-128 data sector installed and verified",
        "noop": "ACCEPTED: exact allocation-128 data sector already present; no write",
        "refused": "REFUSED: fixed allocation-128 data-install gate did not pass",
    },
    "boundary128-data-restore": {
        "stem": "boundary128-data-restore", "chunk": "data-original-sector-00c000-chunk",
        "binary": "boundary128_data_restore", "arm": "0x41524d4c", "magic": "0x4b573852",
        "directory": "kw520-boundary128-probe", "label": "BOUNDARY128_DATA_RESTORE",
        "buffer": "0xf154670a", "target": "0x1f18aa83", "final": "0xf154670a",
        "title": "Restore only fixed sector 0x00c000 from allocation 128 to exact all-FF.",
        "accepted": "ACCEPTED: allocation-128 data sector restored to all-FF",
        "noop": "ACCEPTED: allocation-128 data sector already all-FF; no write",
        "refused": "REFUSED: fixed allocation-128 data-restore gate did not pass",
    },
    "boundary128-pointer-install": {
        "stem": "boundary128-pointer-install", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "overmax_pointer_install", "arm": "0x41524d49", "magic": "0x4b574f50",
        "directory": "kw520-boundary128-probe", "label": "BOUNDARY128_POINTER_INSTALL",
        "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f",
        "title": "Point the main title only to the fixed allocation-128 record at 0x00c000.",
        "accepted": "ACCEPTED: exact allocation-128 title pointer installed and verified",
        "noop": "ACCEPTED: exact allocation-128 title pointer already present; no write",
        "refused": "REFUSED: fixed allocation-128 pointer-install gate did not pass",
    },
    "boundary128-pointer-restore": {
        "stem": "boundary128-pointer-restore", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "overmax_pointer_restore", "arm": "0x41524d4a", "magic": "0x4b574f52",
        "directory": "kw520-boundary128-probe", "label": "BOUNDARY128_POINTER_RESTORE",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372",
        "title": "Restore the main-title pointer before erasing the allocation-128 data sector.",
        "accepted": "ACCEPTED: exact allocation-128 title pointer restored and verified",
        "noop": "ACCEPTED: original title pointer already present; no write",
        "refused": "REFUSED: fixed allocation-128 pointer-restore gate did not pass",
    },
    "boundary128-pointer-restore-retry": {
        "stem": "boundary128-pointer-restore-retry", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary128_pointer_restore_retry", "arm": "0x41524d4d", "magic": "0x4b575852",
        "directory": "kw520-boundary128-probe", "label": "BOUNDARY128_POINTER_RESTORE_RETRY",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372", "status_retry": True,
        "title": "Restore the allocation-128 title pointer with at most two verified status-clear attempts.",
        "accepted": "ACCEPTED: allocation-128 title pointer restored with bounded status retry",
        "noop": "ACCEPTED: original title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-128 pointer-restore gate did not pass",
    },
    "boundary160-data-install": {
        "stem": "boundary160-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary160_data_install", "arm": "0x41524d4e", "magic": "0x4b573649",
        "directory": "kw520-boundary160-probe", "label": "BOUNDARY160_DATA_INSTALL",
        "buffer": "0x0c91e3d5", "target": "0x1f18aa83", "final": "0x0c91e3d5", "status_retry": True,
        "title": "Replace only the inactive allocation-128 record with fixed allocation 160.",
        "accepted": "ACCEPTED: direct allocation-128 to allocation-160 transition verified",
        "noop": "ACCEPTED: exact allocation-160 data sector already present; no write",
        "refused": "REFUSED: fixed allocation-160 data-install gate did not pass",
    },
    "boundary160-pointer-install-retry": {
        "stem": "boundary160-pointer-install-retry", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "boundary_pointer_install_retry", "arm": "0x41524d4f", "magic": "0x4b575849",
        "directory": "kw520-boundary160-probe", "label": "BOUNDARY160_POINTER_INSTALL_RETRY",
        "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f", "status_retry": True,
        "title": "Point the main title to allocation 160 with at most two verified status-clear attempts.",
        "accepted": "ACCEPTED: allocation-160 title pointer installed with bounded status retry",
        "noop": "ACCEPTED: allocation-160 title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-160 pointer-install gate did not pass",
    },
    "boundary160-pointer-restore-retry": {
        "stem": "boundary160-pointer-restore-retry", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary128_pointer_restore_retry", "arm": "0x41524d4d", "magic": "0x4b575852",
        "directory": "kw520-boundary160-probe", "label": "BOUNDARY160_POINTER_RESTORE_RETRY",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372", "status_retry": True,
        "title": "Restore the allocation-160 title pointer with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-160 title pointer restored with bounded status retry",
        "noop": "ACCEPTED: original title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-160 pointer-restore gate did not pass",
    },
    "boundary192-data-install": {
        "stem": "boundary192-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary192_data_install", "arm": "0x41524d50", "magic": "0x4b573749",
        "directory": "kw520-boundary192-probe", "label": "BOUNDARY192_DATA_INSTALL",
        "buffer": "0x80fff2a8", "target": "0x0c91e3d5", "final": "0x80fff2a8", "status_retry": True,
        "title": "Replace only the inactive allocation-160 record with fixed allocation 192.",
        "accepted": "ACCEPTED: direct allocation-160 to allocation-192 transition verified",
        "noop": "ACCEPTED: exact allocation-192 data sector already present; no write",
        "refused": "REFUSED: fixed allocation-192 data-install gate did not pass",
    },
    "boundary192-pointer-install-retry": {
        "stem": "boundary192-pointer-install-retry", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "boundary_pointer_install_retry", "arm": "0x41524d4f", "magic": "0x4b575849",
        "directory": "kw520-boundary192-probe", "label": "BOUNDARY192_POINTER_INSTALL_RETRY",
        "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f", "status_retry": True,
        "title": "Point the main title to allocation 192 with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-192 title pointer installed with bounded status retry",
        "noop": "ACCEPTED: allocation-192 title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-192 pointer-install gate did not pass",
    },
    "boundary192-pointer-restore-retry": {
        "stem": "boundary192-pointer-restore-retry", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary128_pointer_restore_retry", "arm": "0x41524d4d", "magic": "0x4b575852",
        "directory": "kw520-boundary192-probe", "label": "BOUNDARY192_POINTER_RESTORE_RETRY",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372", "status_retry": True,
        "title": "Restore the allocation-192 title pointer with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-192 title pointer restored with bounded status retry",
        "noop": "ACCEPTED: original title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-192 pointer-restore gate did not pass",
    },
    "boundary224-data-install": {
        "stem": "boundary224-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary224_data_install", "arm": "0x41524d51", "magic": "0x4b574149",
        "directory": "kw520-boundary224-probe", "label": "BOUNDARY224_DATA_INSTALL",
        "buffer": "0xff988d5c", "target": "0x80fff2a8", "final": "0xff988d5c", "status_retry": True,
        "title": "Replace only the inactive allocation-192 record with fixed allocation 224.",
        "accepted": "ACCEPTED: direct allocation-192 to allocation-224 transition verified",
        "noop": "ACCEPTED: exact allocation-224 data sector already present; no write",
        "refused": "REFUSED: fixed allocation-224 data-install gate did not pass",
    },
    "boundary224-data-audit": {
        "stem": "boundary224-data-audit", "chunk": "data-previous-sector-00c000-chunk",
        "binary": "boundary_data_audit", "arm": "0x41524d52", "magic": "0x4b574144",
        "directory": "kw520-boundary224-probe", "label": "BOUNDARY224_DATA_AUDIT",
        "buffer": "0x80fff2a8", "target": "0x00000000", "final": "0x00000000", "audit_only": True,
        "title": "Read only the uncertain sector 0x00c000 CRC after the refused allocation-224 erase.",
        "accepted": "ACCEPTED: read-only allocation-224 data-sector audit completed",
        "noop": "ACCEPTED: read-only allocation-224 data-sector audit completed",
        "refused": "REFUSED: read-only allocation-224 data-sector audit gate did not pass",
    },
    "boundary224-data-install-erased": {
        "stem": "boundary224-data-install-erased", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary224_data_install_erased", "arm": "0x41524d53", "magic": "0x4b574145",
        "directory": "kw520-boundary224-probe", "label": "BOUNDARY224_DATA_INSTALL_ERASED",
        "buffer": "0xff988d5c", "target": "0xf154670a", "final": "0xff988d5c", "status_retry": True,
        "title": "Install fixed allocation 224 only from the audited all-FF sector state.",
        "accepted": "ACCEPTED: allocation-224 installed from audited all-FF sector",
        "noop": "ACCEPTED: exact allocation-224 data sector already present; no write",
        "refused": "REFUSED: all-FF to allocation-224 recovery gate did not pass",
    },
    "boundary224-pointer-install-retry": {
        "stem": "boundary224-pointer-install-retry", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "boundary_pointer_install_retry", "arm": "0x41524d4f", "magic": "0x4b575849",
        "directory": "kw520-boundary224-probe", "label": "BOUNDARY224_POINTER_INSTALL_RETRY",
        "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f", "status_retry": True,
        "title": "Point the main title to allocation 224 with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-224 title pointer installed with bounded status retry",
        "noop": "ACCEPTED: allocation-224 title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-224 pointer-install gate did not pass",
    },
    "boundary224-pointer-restore-retry": {
        "stem": "boundary224-pointer-restore-retry", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary128_pointer_restore_retry", "arm": "0x41524d4d", "magic": "0x4b575852",
        "directory": "kw520-boundary224-probe", "label": "BOUNDARY224_POINTER_RESTORE_RETRY",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372", "status_retry": True,
        "title": "Restore the allocation-224 title pointer with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-224 title pointer restored with bounded status retry",
        "noop": "ACCEPTED: original title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-224 pointer-restore gate did not pass",
    },
    "boundary240-data-install": {
        "stem": "boundary240-data-install", "chunk": "data-test-sector-00c000-chunk",
        "binary": "boundary240_data_install", "arm": "0x41524d54", "magic": "0x4b574249",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_DATA_INSTALL",
        "buffer": "0xaba2265e", "target": "0xff988d5c", "final": "0xaba2265e", "status_retry": True,
        "title": "Replace only the inactive allocation-224 record with fixed allocation 240.",
        "accepted": "ACCEPTED: direct allocation-224 to allocation-240 transition verified",
        "noop": "ACCEPTED: exact allocation-240 data sector already present; no write",
        "refused": "REFUSED: fixed allocation-240 data-install gate did not pass",
    },
    "boundary240-data-restore": {
        "stem": "boundary240-data-restore", "chunk": "data-original-sector-00c000-chunk",
        "binary": "boundary240_data_restore", "arm": "0x41524d55", "magic": "0x4b574346",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_DATA_RESTORE",
        "buffer": "0xf154670a", "target": "0xaba2265e", "final": "0xf154670a", "status_retry": True,
        "long_wait": True,
        "title": "Restore only the now-unreferenced allocation-240 data sector to exact all-FF.",
        "accepted": "ACCEPTED: allocation-240 data sector restored to exact all-FF",
        "noop": "ACCEPTED: allocation-240 data sector already exact all-FF; no write",
        "refused": "REFUSED: fixed allocation-240 data-restore gate did not pass",
    },
    "boundary240-pointer-audit": {
        "stem": "boundary240-pointer-audit", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary_pointer_audit", "arm": "0x41524d56", "magic": "0x4b575041",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_AUDIT",
        "buffer": "0xf5c23372", "target": "0x00000000", "final": "0x00000000", "audit_only": True, "recover_spi": True,
        "title": "Read only the partial pointer-sector CRC after interrupted final restore.",
        "accepted": "ACCEPTED: read-only partial pointer-sector audit completed",
        "noop": "ACCEPTED: read-only partial pointer-sector audit completed",
        "refused": "REFUSED: read-only partial pointer-sector audit gate did not pass",
    },
    "boundary240-pointer-bitbang-audit": {
        "stem": "boundary240-pointer-bitbang-audit", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary_pointer_bitbang_audit", "arm": "0x41524d57", "magic": "0x4b574241",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_BITBANG_AUDIT",
        "buffer": "0xf5c23372", "target": "0x00000000", "final": "0x00000000", "audit_only": True, "recover_bitbang": True,
        "title": "Read only the partial pointer-sector CRC through bounded GPIO SPI mode 0.",
        "accepted": "ACCEPTED: read-only bitbang partial pointer-sector audit completed",
        "noop": "ACCEPTED: read-only bitbang partial pointer-sector audit completed",
        "refused": "REFUSED: read-only bitbang partial pointer-sector audit gate did not pass",
    },
    "boundary240-pointer-interrupted-audit": {
        "stem": "boundary240-pointer-interrupted-audit", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary_pointer_interrupted_audit", "arm": "0x41524d59", "magic": "0x4b574249",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_INTERRUPTED_AUDIT",
        "buffer": "0xf5c23372", "target": "0x00000000", "final": "0x00000000",
        "status": "0x02", "audit_only": True, "recover_bitbang": True,
        "title": "Read the exact sector after a host-timeout halt with status 0x02.",
        "accepted": "ACCEPTED: read-only interrupted pointer-sector audit completed",
        "noop": "ACCEPTED: read-only interrupted pointer-sector audit completed",
        "refused": "REFUSED: read-only interrupted pointer-sector audit gate did not pass",
    },
    "boundary240-pointer-interrupted-restore": {
        "stem": "boundary240-pointer-interrupted-restore", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary_pointer_interrupted_restore", "arm": "0x41524d5a", "magic": "0x4b574952",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_INTERRUPTED_RESTORE",
        "buffer": "0xf5c23372", "target": "0x559db759", "final": "0xf5c23372",
        "status": "0x02", "recover_bitbang": True, "long_wait": True,
        "title": "Recover the exact status-0x02 interrupted pointer sector through bitbang SPI.",
        "accepted": "ACCEPTED: interrupted pointer sector recovered and verified through bitbang SPI",
        "noop": "ACCEPTED: original pointer sector already present; interrupted recovery made no write",
        "refused": "REFUSED: interrupted pointer-sector recovery gate did not pass",
    },
    "boundary240-pointer-bitbang-restore": {
        "stem": "boundary240-pointer-bitbang-restore", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary_pointer_bitbang_restore", "arm": "0x41524d58", "magic": "0x4b574252",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_BITBANG_RESTORE",
        "buffer": "0xf5c23372", "target": "0x33e293e2", "final": "0xf5c23372",
        "status_retry": True, "recover_bitbang": True,
        "title": "Recover the exact partially programmed pointer sector using fixed GPIO bitbang SPI.",
        "accepted": "ACCEPTED: partial pointer sector recovered and verified through bitbang SPI",
        "noop": "ACCEPTED: original pointer sector already present; recovery helper made no write",
        "refused": "REFUSED: bitbang pointer-sector recovery gate did not pass",
    },
    "boundary240-pointer-install-retry": {
        "stem": "boundary240-pointer-install-retry", "chunk": "pointer-test-sector-003000-chunk",
        "binary": "boundary_pointer_install_retry", "arm": "0x41524d4f", "magic": "0x4b575849",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_INSTALL_RETRY",
        "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f", "status_retry": True,
        "title": "Point the main title to allocation 240 with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-240 title pointer installed with bounded status retry",
        "noop": "ACCEPTED: allocation-240 title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-240 pointer-install gate did not pass",
    },
    "boundary240-pointer-restore-retry": {
        "stem": "boundary240-pointer-restore-retry", "chunk": "pointer-original-sector-003000-chunk",
        "binary": "boundary128_pointer_restore_retry", "arm": "0x41524d4d", "magic": "0x4b575852",
        "directory": "kw520-boundary240-probe", "label": "BOUNDARY240_POINTER_RESTORE_RETRY",
        "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372", "status_retry": True,
        "title": "Restore the allocation-240 title pointer with the qualified bounded helper.",
        "accepted": "ACCEPTED: allocation-240 title pointer restored with bounded status retry",
        "noop": "ACCEPTED: original title pointer already present; bounded helper made no write",
        "refused": "REFUSED: bounded allocation-240 pointer-restore gate did not pass",
    },
}

FRONTIER_CRCS = {
    256: "0x28017863",
    320: "0x41b76a28",
    384: "0x52fdfc69",
    448: "0x7cfe1846",
    480: "0xebdaf776",
    512: "0x72628a3a",
}
for allocation, crc in FRONTIER_CRCS.items():
    suffix = f"{allocation:04x}"
    VARIANTS[f"frontier{allocation}-data-install"] = {
        "stem": f"frontier{allocation}-data-install",
        "chunk": f"alloc-{allocation}-data-test-sector-00c000-chunk",
        "binary": f"frontier{allocation}_data_install",
        "arm": f"0x4149{suffix}", "magic": f"0x4b46{suffix}",
        "directory": "kw520-stack-frontier", "label": f"FRONTIER{allocation}_DATA_INSTALL",
        "buffer": crc, "target": "0xf154670a", "final": crc,
        "status_retry": True, "long_wait": True, "helper_readback": "0x700",
        "title": f"Install only the fixed cyclic allocation-{allocation} record in the inactive data sector.",
        "accepted": f"ACCEPTED: cyclic allocation-{allocation} data sector installed and verified",
        "noop": f"ACCEPTED: cyclic allocation-{allocation} data sector already present; no write",
        "refused": f"REFUSED: cyclic allocation-{allocation} data-install gate did not pass",
    }
    VARIANTS[f"frontier{allocation}-data-restore"] = {
        "stem": f"frontier{allocation}-data-restore", "chunk": "data-original-sector-00c000-chunk",
        "binary": f"frontier{allocation}_data_restore",
        "arm": f"0x4152{suffix}", "magic": f"0x4b52{suffix}",
        "directory": "kw520-stack-frontier", "label": f"FRONTIER{allocation}_DATA_RESTORE",
        "buffer": "0xf154670a", "target": crc, "final": "0xf154670a",
        "status_retry": True, "long_wait": True, "helper_readback": "0x700",
        "title": f"Restore only the inactive allocation-{allocation} data sector to exact all-FF.",
        "accepted": f"ACCEPTED: allocation-{allocation} data sector restored to exact all-FF",
        "noop": f"ACCEPTED: allocation-{allocation} data sector already exact all-FF; no write",
        "refused": f"REFUSED: allocation-{allocation} data-restore gate did not pass",
    }

VARIANTS["frontier-pointer-install"] = {
    "stem": "frontier-pointer-install", "chunk": "pointer-test-sector-003000-chunk",
    "binary": "boundary_pointer_install_retry", "arm": "0x41524d4f", "magic": "0x4b575849",
    "directory": "kw520-stack-frontier", "label": "FRONTIER_POINTER_INSTALL",
    "buffer": "0x6f68933f", "target": "0xf5c23372", "final": "0x6f68933f",
    "status_retry": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Activate the fixed stack-frontier record only after its data sector is verified.",
    "accepted": "ACCEPTED: stack-frontier title pointer installed and verified",
    "noop": "ACCEPTED: stack-frontier title pointer already present; no write",
    "refused": "REFUSED: stack-frontier pointer-install gate did not pass",
}
VARIANTS["frontier-pointer-bitbang-restore"] = {
    "stem": "frontier-pointer-bitbang-restore", "chunk": "pointer-original-sector-003000-chunk",
    "binary": "frontier_pointer_bitbang_restore", "arm": "0x41524d5b", "magic": "0x4b574652",
    "directory": "kw520-stack-frontier", "label": "FRONTIER_POINTER_BITBANG_RESTORE",
    "buffer": "0xf5c23372", "target": "0x6f68933f", "final": "0xf5c23372",
    "status_retry": True, "recover_bitbang": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Restore the stack-frontier pointer without depending on the crashed firmware SPI setup.",
    "accepted": "ACCEPTED: stack-frontier title pointer restored through bitbang SPI",
    "noop": "ACCEPTED: original title pointer already present; bitbang helper made no write",
    "refused": "REFUSED: stack-frontier bitbang pointer-restore gate did not pass",
}

VARIANTS["language9-install"] = {
    "stem": "language9-install", "chunk": "language9-test-sector-003000-chunk",
    "binary": "language9_install", "arm": "0x41524d5c", "magic": "0x4b574e49",
    "directory": "kw520-language-gate", "label": "LANGUAGE9_INSTALL",
    "buffer": "0xfa2d76bb", "target": "0xf5c23372", "final": "0xfa2d76bb",
    "status_retry": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Install one valid duplicate language descriptor and change only the declared count from 8 to 9.",
    "accepted": "ACCEPTED: exact valid language-9 directory sector installed",
    "noop": "ACCEPTED: exact language-9 directory sector already present; no write",
    "refused": "REFUSED: language-9 install gate did not pass",
}
VARIANTS["language9-restore"] = {
    "stem": "language9-restore", "chunk": "original-sector-003000-chunk",
    "binary": "language9_restore", "arm": "0x41524d5d", "magic": "0x4b574e52",
    "directory": "kw520-language-gate", "label": "LANGUAGE9_RESTORE",
    "buffer": "0xf5c23372", "target": "0xfa2d76bb", "final": "0xf5c23372",
    "status_retry": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Restore the exact original 8-language directory sector after one observation.",
    "accepted": "ACCEPTED: exact original 8-language directory sector restored",
    "noop": "ACCEPTED: exact original 8-language directory sector already present; no write",
    "refused": "REFUSED: language-9 restore gate did not pass",
}
VARIANTS["language9-list-install"] = {
    "stem": "language9-list-install", "chunk": "language9-listed-test-sector-003000-chunk",
    "binary": "language9_list_install", "arm": "0x41524d5e", "magic": "0x4b574c49",
    "directory": "kw520-language-list-gate", "label": "LANGUAGE9_LIST_INSTALL",
    "buffer": "0x4779b7f4", "target": "0xf5c23372", "final": "0x4779b7f4",
    "status_retry": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Install a consistent ninth language in both the active-ID list and sparse descriptor directory.",
    "accepted": "ACCEPTED: exact consistent language-9 list sector installed",
    "noop": "ACCEPTED: exact consistent language-9 list sector already present; no write",
    "refused": "REFUSED: consistent language-9 list install gate did not pass",
}
VARIANTS["language9-list-restore"] = {
    "stem": "language9-list-restore", "chunk": "original-sector-003000-chunk",
    "binary": "language9_list_restore", "arm": "0x41524d5f", "magic": "0x4b574c52",
    "directory": "kw520-language-list-gate", "label": "LANGUAGE9_LIST_RESTORE",
    "buffer": "0xf5c23372", "target": "0x4779b7f4", "final": "0xf5c23372",
    "status_retry": True, "long_wait": True, "helper_readback": "0x700",
    "title": "Restore the exact original sector after the consistent ninth-language SRAM observation.",
    "accepted": "ACCEPTED: exact original sector restored after language-list probe",
    "noop": "ACCEPTED: exact original language sector already present; no write",
    "refused": "REFUSED: language-list restore gate did not pass",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_exact(text: str, old: str, new: str, count: int) -> str:
    actual = text.count(old)
    if actual != count:
        raise ValueError(f"template token count {actual}, expected {count}: {old!r}")
    return text.replace(old, new)


def derive(template: bytes, mode: str) -> str:
    digest = sha256(template)
    if digest != TEMPLATE_SHA256:
        raise ValueError(f"refusing changed restore template {digest}")
    cfg = VARIANTS[mode]
    text = template.decode("utf-8")
    text = replace_exact(
        text,
        "# Qualify the fixed sector-restoration helper against an already-correct sector.\n"
        "# Accepted result is state 0x42: no Write Enable, erase, or program executed.",
        f"# {cfg['title']}\n# Only exact address-and-CRC-gated states are accepted.",
        1,
    )
    text = replace_exact(text, "restore-noop-", f"{cfg['stem']}-", 27)
    text = replace_exact(
        text,
        "build/kw520-format-probe/restore-sector-003000-chunk",
        f"build/{cfg.get('directory', 'kw520-overmax-probe')}/{cfg['chunk']}",
        4,
    )
    text = replace_exact(text, "build/kw520-spi-patch/restore_sector.bin", f"build/kw520-spi-patch/{cfg['binary']}.bin", 1)
    text = replace_exact(text, "0x41524d32", cfg["arm"], 1)
    text = replace_exact(text, "RESTORE_NOOP", cfg["label"], 1)
    if cfg.get("helper_readback"):
        text = replace_exact(
            text,
            "helper-readback.bin 0x20001a00 0x6cc",
            f"helper-readback.bin 0x20001a00 {cfg['helper_readback']}",
            1,
        )
    if cfg.get("recover_spi"):
        text = replace_exact(
            text,
            "init\nhalt 500\nrefresh_wdt",
            "init\nhalt 500\n"
            "set rec_acfgr [lindex [read_memory 0x48000000 32 1] 0]\n"
            "set rec_aodt [lindex [read_memory 0x48000014 32 1] 0]\n"
            "set rec_bcfgr [lindex [read_memory 0x48000400 32 1] 0]\n"
            "set rec_bpull [lindex [read_memory 0x4800040c 32 1] 0]\n"
            "set rec_bmuxh [lindex [read_memory 0x48000424 32 1] 0]\n"
            "set rec_ctrl1 [lindex [read_memory 0x40003800 32 1] 0]\n"
            "set rec_ctrl2 [lindex [read_memory 0x40003804 32 1] 0]\n"
            "set rec_ahben [lindex [read_memory 0x40021014 32 1] 0]\n"
            "set rec_apb1en [lindex [read_memory 0x4002101c 32 1] 0]\n"
            "write_memory 0x40021014 32 [list [expr {$rec_ahben | 0x00060000}]]\n"
            "write_memory 0x4002101c 32 [list [expr {$rec_apb1en | 0x00004000}]]\n"
            "write_memory 0x48000000 32 [list [expr {($rec_acfgr & ~(3 << 16)) | (1 << 16)}]]\n"
            "write_memory 0x48000018 32 {0x00000100}\n"
            "write_memory 0x48000400 32 [list [expr {($rec_bcfgr & ~(0x3f << 26)) | (0x2a << 26)}]]\n"
            "write_memory 0x4800040c 32 [list [expr {($rec_bpull & ~(0x3f << 26)) | (0x04 << 26)}]]\n"
            "write_memory 0x48000424 32 [list [expr {$rec_bmuxh & 0x000fffff}]]\n"
            "write_memory 0x40003800 32 {0x00000357}\n"
            "refresh_wdt",
            1,
        )
        text = replace_exact(
            text,
            'puts [format "RESTORED_VTOR=0x%08x" [lindex $old_vtor 0]]\nshutdown',
            "write_memory 0x40003800 32 {0}\n"
            "write_memory 0x48000424 32 [list $rec_bmuxh]\n"
            "write_memory 0x4800040c 32 [list $rec_bpull]\n"
            "write_memory 0x48000400 32 [list $rec_bcfgr]\n"
            "write_memory 0x48000014 32 [list $rec_aodt]\n"
            "write_memory 0x48000000 32 [list $rec_acfgr]\n"
            "write_memory 0x40003804 32 [list $rec_ctrl2]\n"
            "write_memory 0x40003800 32 [list $rec_ctrl1]\n"
            "write_memory 0x4002101c 32 [list $rec_apb1en]\n"
            "write_memory 0x40021014 32 [list $rec_ahben]\n"
            'puts [format "RESTORED_VTOR=0x%08x" [lindex $old_vtor 0]]\nshutdown',
            1,
        )
    if cfg.get("recover_bitbang"):
        text = replace_exact(
            text,
            "init\nhalt 500\nrefresh_wdt",
            "init\nhalt 500\n"
            "set rec_acfgr [lindex [read_memory 0x48000000 32 1] 0]\n"
            "set rec_aomode [lindex [read_memory 0x48000004 32 1] 0]\n"
            "set rec_aodrvr [lindex [read_memory 0x48000008 32 1] 0]\n"
            "set rec_apull [lindex [read_memory 0x4800000c 32 1] 0]\n"
            "set rec_aodt [lindex [read_memory 0x48000014 32 1] 0]\n"
            "set rec_bcfgr [lindex [read_memory 0x48000400 32 1] 0]\n"
            "set rec_bomode [lindex [read_memory 0x48000404 32 1] 0]\n"
            "set rec_bodrvr [lindex [read_memory 0x48000408 32 1] 0]\n"
            "set rec_bpull [lindex [read_memory 0x4800040c 32 1] 0]\n"
            "set rec_bodt [lindex [read_memory 0x48000414 32 1] 0]\n"
            "set rec_ahben [lindex [read_memory 0x40021014 32 1] 0]\n"
            "write_memory 0x40021014 32 [list [expr {$rec_ahben | 0x00060000}]]\n"
            "write_memory 0x48000018 32 {0x00000100}\n"
            "write_memory 0x48000428 32 {0x00002000}\n"
            "write_memory 0x48000418 32 {0x00008000}\n"
            "write_memory 0x48000004 32 [list [expr {$rec_aomode & ~0x00000100}]]\n"
            "write_memory 0x48000008 32 [list [expr {($rec_aodrvr & ~(3 << 16)) | (1 << 16)}]]\n"
            "write_memory 0x48000404 32 [list [expr {$rec_bomode & ~0x0000a000}]]\n"
            "write_memory 0x48000408 32 [list [expr {($rec_bodrvr & ~(0x33 << 26)) | (0x11 << 26)}]]\n"
            "write_memory 0x4800040c 32 [list [expr {($rec_bpull & ~(0x3f << 26)) | (0x04 << 26)}]]\n"
            "write_memory 0x48000000 32 [list [expr {($rec_acfgr & ~(3 << 16)) | (1 << 16)}]]\n"
            "write_memory 0x48000400 32 [list [expr {($rec_bcfgr & ~(0x3f << 26)) | (0x11 << 26)}]]\n"
            "refresh_wdt",
            1,
        )
        text = replace_exact(
            text,
            "set acfgr [lindex [read_memory 0x48000000 32 1] 0]\n"
            "set aodt [lindex [read_memory 0x48000014 32 1] 0]\n"
            "set bcfgr [lindex [read_memory 0x48000400 32 1] 0]\n"
            "set ctrl1 [lindex [read_memory 0x40003800 32 1] 0]\n"
            "set sts [lindex [read_memory 0x40003808 32 1] 0]\n"
            "set ahben [lindex [read_memory 0x40021014 32 1] 0]\n"
            "set apb1en [lindex [read_memory 0x4002101c 32 1] 0]\n"
            "set live_ok [expr {\n"
            "    (($acfgr >> 16) & 3) == 1 && ($aodt & 0x100) != 0 &&\n"
            "    (($bcfgr >> 26) & 3) == 2 && (($bcfgr >> 28) & 3) == 2 &&\n"
            "    (($bcfgr >> 30) & 3) == 2 && ($ctrl1 & 0xffff) == 0x357 &&\n"
            "    ($sts & 2) != 0 && ($ahben & 0x40000) != 0 && ($apb1en & 0x4000) != 0\n"
            "}]\n"
            "puts [format \"LIVE_REGS ok=%u acfgr=%08x aodt=%08x bcfgr=%08x ctrl1=%08x sts=%08x\" $live_ok $acfgr $aodt $bcfgr $ctrl1 $sts]\n"
            "if {!$live_ok} {\n"
            "    puts \"REFUSED: live PA8/SPI2 configuration is not present\"\n"
            "    shutdown\n"
            "}",
            "set acfgr [lindex [read_memory 0x48000000 32 1] 0]\n"
            "set aodt [lindex [read_memory 0x48000014 32 1] 0]\n"
            "set bcfgr [lindex [read_memory 0x48000400 32 1] 0]\n"
            "set bodt [lindex [read_memory 0x48000414 32 1] 0]\n"
            "set ahben [lindex [read_memory 0x40021014 32 1] 0]\n"
            "set live_ok [expr {\n"
            "    (($acfgr >> 16) & 3) == 1 && ($aodt & 0x100) != 0 &&\n"
            "    (($bcfgr >> 26) & 3) == 1 && (($bcfgr >> 28) & 3) == 0 &&\n"
            "    (($bcfgr >> 30) & 3) == 1 && ($bodt & 0x2000) == 0 &&\n"
            "    ($bodt & 0x8000) != 0 && ($ahben & 0x60000) == 0x60000\n"
            "}]\n"
            "puts [format \"BITBANG_REGS ok=%u acfgr=%08x aodt=%08x bcfgr=%08x bodt=%08x\" $live_ok $acfgr $aodt $bcfgr $bodt]\n"
            "if {!$live_ok} {\n"
            "    puts \"REFUSED: fixed PA8/PB13/PB14/PB15 bitbang roles are not present\"\n"
            "    shutdown\n"
            "}",
            1,
        )
        text = replace_exact(
            text,
            'puts [format "RESTORED_VTOR=0x%08x" [lindex $old_vtor 0]]\nshutdown',
            "write_memory 0x48000400 32 [list $rec_bcfgr]\n"
            "write_memory 0x48000000 32 [list $rec_acfgr]\n"
            "write_memory 0x4800040c 32 [list $rec_bpull]\n"
            "write_memory 0x48000408 32 [list $rec_bodrvr]\n"
            "write_memory 0x48000404 32 [list $rec_bomode]\n"
            "write_memory 0x48000414 32 [list $rec_bodt]\n"
            "write_memory 0x4800000c 32 [list $rec_apull]\n"
            "write_memory 0x48000008 32 [list $rec_aodrvr]\n"
            "write_memory 0x48000004 32 [list $rec_aomode]\n"
            "write_memory 0x48000014 32 [list $rec_aodt]\n"
            "write_memory 0x40021014 32 [list $rec_ahben]\n"
            'puts [format "RESTORED_VTOR=0x%08x" [lindex $old_vtor 0]]\nshutdown',
            1,
        )
    if cfg.get("audit_only"):
        text = replace_exact(
            text,
            "if {$state == 0x41 || $state == 0x42 || $state >= 0xe0} {",
            "if {$state == 0x41 || $state == 0x42 || $state == 0x43 || $state >= 0xe0} {",
            1,
        )
    if cfg.get("long_wait"):
        text = replace_exact(text, "for {set i 0} {$i < 500} {incr i} {", "for {set i 0} {$i < 4000} {incr i} {", 1)
    noop = OLD_NOOP.replace("0x4b575052", cfg["magic"]).replace(
        "0xf5c23372 && $target_crc == 0xf5c23372",
        f"{cfg['buffer']} && $target_crc == {cfg['final']}",
    )
    expected_status = cfg.get("status", "0x18")
    noop = noop.replace("$status == 0x18", f"$status == {expected_status}")
    write = (
        "set restore_ok [expr {$core_ok && $done && $magic == " + cfg["magic"]
        + " && $state == 0x41 && $jedec == 0x1c3016 && $status == " + expected_status + " && $protection == 0xff && $buffer_crc == " + cfg["buffer"]
        + " && $target_crc == " + cfg["target"]
        + " && $erased_crc == 0xf154670a && $final_crc == " + cfg["final"]
        + " && $pages == 16 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0x18 && $cleanup == 0}]"
    )
    if cfg.get("audit_only"):
        noop = (
            "set noop_ok [expr {$core_ok && $done && $magic == " + cfg["magic"]
            + " && $state == 0x43 && $jedec == 0x1c3016 && $status == " + expected_status + " && $protection == 0xff && $buffer_crc == " + cfg["buffer"]
            + " && $erased_crc == 0 && $final_crc == 0 && $pages == 0 && $status_last == 0 && $spi_error == 0 && $status_cleared == 0 && $status_restored == 0 && $cleanup == 0}]"
        )
        write = "set restore_ok 0"
    if cfg.get("status_retry"):
        text = replace_exact(
            text,
            "set cleanup [lindex [read_memory 0x20002158 32 1] 0]",
            "set cleanup [lindex [read_memory 0x20002158 32 1] 0]\n"
            "set status_attempts [lindex [read_memory 0x2000215c 32 1] 0]\n"
            "set status_wren_last [lindex [read_memory 0x20002160 32 1] 0]",
            1,
        )
        noop = noop.replace("&& $cleanup == 0}]", "&& $cleanup == 0 && $status_attempts == 0 && $status_wren_last == 0}]")
        write = write.replace(
            "&& $cleanup == 0}]",
            "&& $cleanup == 0 && $status_attempts >= 1 && $status_attempts <= 2 && $status_wren_last == 0x1a}]",
        )
    text = replace_exact(text, OLD_NOOP, noop, 1)
    text = replace_exact(text, OLD_WRITE, write, 1)
    if cfg.get("status_retry"):
        lines = text.splitlines()
        result: list[str] = []
        inserted = 0
        prefix = f'puts [format "{cfg["label"]} '
        for line in lines:
            result.append(line)
            if line.startswith(prefix):
                result.append('puts [format "STATUS_CLEAR_RETRY attempts=%u wren_last=%02x" $status_attempts $status_wren_last]')
                inserted += 1
        if inserted != 1:
            raise ValueError(f"retry telemetry insertion count {inserted}, expected 1")
        text = "\n".join(result) + "\n"
    text = replace_exact(text, 'puts "ACCEPTED: fixed restore helper exited before Write Enable"', f'puts "{cfg["noop"]}"', 1)
    text = replace_exact(text, 'puts "ACCEPTED: exact format-probe sector restored and verified"', f'puts "{cfg["accepted"]}"', 1)
    text = replace_exact(text, 'puts "REFUSED: fixed restore no-op gate did not pass"', f'puts "{cfg["refused"]}"', 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=tuple(VARIANTS), required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"refusing to replace {args.output}; use --force")
    output = derive(args.template.read_bytes(), args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} ({sha256(output.encode('utf-8'))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
