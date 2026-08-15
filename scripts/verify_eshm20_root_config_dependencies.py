# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify receipted ESHM20 root bytes before offline dependency parsing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.openquake_config_dependencies import OpenQuakeConfigError, extract_openquake_config_references
except ModuleNotFoundError:  # pragma: no cover
    from openquake_config_dependencies import OpenQuakeConfigError, extract_openquake_config_references

SCHEMA_VERSION = "oc-eshm20-root-dependency-bridge-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
PREFIX = "oq_computational/oq_configuration_eshm20_v12e_region_main/"
REPOSITORY_PATH = PREFIX + "config_eshm20_v12e_main_region.ini"
EXPECTED_BYTE_COUNT = 2719
EXPECTED_SHA256 = "f1f4dabc48e1b8a478dbdb96b01c8f58cc68c98abd6f9004671c5fba9eb7e714"
PARSER_ID = "scripts.openquake_config_dependencies.extract_openquake_config_references"
INVENTORY_RECEIPT_COMMENT_ID = 5290449064

# Exact canonical paths from trusted-main #332 result 5290449064. This is metadata
# authority only: membership never substitutes for a byte receipt.
FROZEN_INVENTORY_PATHS = frozenset(
    PREFIX + suffix
    for suffix in (
        "config_eshm20_v12e_main_region.ini",
        "eshm20_site_model_v06d.csv",
        "gmpe_complete_logic_tree_5br.xml",
        "source_model_logic_tree_eshm20_model_v12e.xml",
        "source_models",
        "source_models/asm_v12e",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
        "source_models/asm_v12e/asm_ver12e_winGT_fs017_twingr.xml",
        "source_models/deep_v12e",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
        "source_models/fsm_v09",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRA_MA_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRA_ML_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRA_MU_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRL_MA_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRL_ML_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRL_MU_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRU_MA_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRU_ML_fMthr.xml",
        "source_models/fsm_v09/fs_ver09e_model_aGR_SRU_MU_fMthr.xml",
        "source_models/interface_v12b",
        "source_models/interface_v12b/CaA_IF2222222_M40.xml",
        "source_models/interface_v12b/CyA_IF2222222_M40.xml",
        "source_models/interface_v12b/GiA_IF2222222_M40.xml",
        "source_models/interface_v12b/HeA_IF2222222_M40.xml",
        "source_models/ssm_v09",
        "source_models/ssm_v09/seis_ver12b_fMthr_asm_ver12e_winGT_fs017_agbrs_point.xml",
        "source_models/volcanic_v12e",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_low.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_mid.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_hi_abgrs_maxmag_upp.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_low.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_mid.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_lo_abgrs_maxmag_upp.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_low.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_mid.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_mid_abgrs_maxmag_upp.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_low.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_mid.xml",
        "source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_pareto_abgrs_cornermag_upp.xml",
    )
)


class VerifiedRootConfigError(ValueError):
    """Raised when root bytes or derived dependencies violate frozen evidence."""


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise VerifiedRootConfigError("root payload must be immutable bytes")
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise VerifiedRootConfigError(
            f"root byte count mismatch: observed {len(payload)}, expected {EXPECTED_BYTE_COUNT}"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != EXPECTED_SHA256:
        raise VerifiedRootConfigError("root SHA-256 mismatch")
    return observed_sha256


def extract_verified_root_dependencies(payload: bytes) -> dict[str, Any]:
    observed_sha256 = _verify_payload_identity(payload)
    try:
        config_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerifiedRootConfigError("verified root payload is not strict UTF-8") from exc
    try:
        references = extract_openquake_config_references(config_text, config_path=REPOSITORY_PATH)
    except OpenQuakeConfigError as exc:
        raise VerifiedRootConfigError(f"verified root dependency parse failed: {exc}") from exc

    if len(FROZEN_INVENTORY_PATHS) != 62:
        raise VerifiedRootConfigError("frozen ESHM20 inventory identity is invalid")
    if any(reference.resolved_path not in FROZEN_INVENTORY_PATHS for reference in references):
        raise VerifiedRootConfigError("verified root dependency is absent from frozen inventory")

    dependencies = [
        {
            "section": reference.section,
            "option": reference.option,
            "raw_path": reference.raw_path,
            "resolved_path": reference.resolved_path,
        }
        for reference in references
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "parser": PARSER_ID,
        "inventory_receipt_comment_id": INVENTORY_RECEIPT_COMMENT_ID,
        "dependencies": dependencies,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _file_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _read_regular_file(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise VerifiedRootConfigError(f"cannot stat root payload: {type(exc).__name__}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise VerifiedRootConfigError("root payload path must be a non-symlink regular file")
    if before.st_size != EXPECTED_BYTE_COUNT:
        raise VerifiedRootConfigError(
            f"root byte count mismatch: observed {before.st_size}, expected {EXPECTED_BYTE_COUNT}"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise VerifiedRootConfigError(f"cannot open root payload: {type(exc).__name__}") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _file_identity(opened) != _file_identity(before):
            raise VerifiedRootConfigError("root payload identity changed before read")
        chunks: list[bytes] = []
        remaining = EXPECTED_BYTE_COUNT + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if _file_identity(after) != _file_identity(opened):
            raise VerifiedRootConfigError("root payload identity changed during read")
    except OSError as exc:
        raise VerifiedRootConfigError(f"cannot read root payload: {type(exc).__name__}") from exc
    finally:
        os.close(fd)
    payload = b"".join(chunks)
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise VerifiedRootConfigError(
            f"root byte count mismatch: observed {len(payload)}, expected {EXPECTED_BYTE_COUNT}"
        )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Local materialized ESHM20 root INI")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = extract_verified_root_dependencies(_read_regular_file(Path(args.input)))
    except VerifiedRootConfigError as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
