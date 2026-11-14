# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GRWL V01.01/V01.02 original-ZIP *member-byte* difference proof.

Uses original-ZIP integrity/structure gate and bounded streamed member SHA-256.
Never extracts, emits or commits third-party source data, and never interprets
changed shapefile bytes as changed river widths without a record-level audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from research_runners.grwl_original_zip_structure_preflight_v0 import (
    OriginalZipError, _safe_members, inspect_original_zip,
)

SCHEMA = 'opencatastrophe-grwl-member-digest-difference-v0'
CHUNK = 1 << 20
CORE_EXTENSIONS = frozenset({'.shp', '.shx', '.dbf', '.prj'})


def member_digests(archive: zipfile.ZipFile) -> dict[str, dict]:
    """Bounded streaming verification of uncompressed member bytes (synthetic-testable)."""
    members = _safe_members(archive)
    digests = {}
    for info in members:
        if info.is_dir():
            continue
        digest = hashlib.sha256()
        count = 0
        try:
            with archive.open(info, 'r') as stream:
                while chunk := stream.read(CHUNK):
                    count += len(chunk)
                    if count > info.file_size:
                        raise OriginalZipError('member expanded beyond declared ZIP size')
                    digest.update(chunk)
        except (zipfile.BadZipFile, RuntimeError, EOFError) as exc:
            raise OriginalZipError('ZIP member decompression or CRC check failed') from exc
        if count != info.file_size:
            raise OriginalZipError('ZIP member content length mismatch')
        digests[info.filename.casefold()] = {
            'member_name': info.filename,
            'uncompressed_bytes': count,
            'sha256_of_uncompressed_member_bytes': digest.hexdigest(),
        }
    return dict(sorted(digests.items()))


def compare_digest_inventories(early: dict[str, dict], late: dict[str, dict]) -> dict:
    """Classify byte differences without making unsupported scientific claims."""
    def equivalent(k: str) -> bool:
        return early[k]['sha256_of_uncompressed_member_bytes'] == late[k]['sha256_of_uncompressed_member_bytes'] and early[k]['uncompressed_bytes'] == late[k]['uncompressed_bytes']

    common = sorted(set(early) & set(late))
    changed = [k for k in common if not equivalent(k)]
    unchanged = [k for k in common if equivalent(k)]
    only_2018 = sorted(set(early) - set(late))
    only_2026 = sorted(set(late) - set(early))
    core_early = {k for k in early if Path(k).suffix in CORE_EXTENSIONS}
    core_late = {k for k in late if Path(k).suffix in CORE_EXTENSIONS}
    all_core_members_equal = (core_early == core_late and len(core_early) == 4
                              and all(equivalent(k) for k in core_early))
    def ext_equal(suffix: str) -> bool:
        a, b = [k for k in early if Path(k).suffix == suffix], [k for k in late if Path(k).suffix == suffix]
        return len(a) == len(b) == 1 and a == b and equivalent(a[0])

    return {
        'schema': SCHEMA,
        'identical_uncompressed_member_payloads': not (changed or only_2018 or only_2026),
        'core_shapefile_bytes_identical': all_core_members_equal,
        'shp_geometry_member_bytes_identical': ext_equal('.shp'),
        'dbf_attribute_member_bytes_identical': ext_equal('.dbf'),
        'member_files_changed': changed,
        'member_files_identical': unchanged,
        'member_files_only_2018': only_2018,
        'member_files_only_2026': only_2026,
        'core_member_identity_is_not_spatial_model_validation': True,
        'any_real_width_change_verified': False,
        'any_real_geometry_change_interpreted': False,
        'flood_hazard_calibrated': False,
        'source_data_admitted': False,
        'production_database_modified': False,
    }


def fingerprint_original(path: Path, release: str) -> tuple[dict, dict]:
    """Original ZIP size/MD5/structure gate, pinned SHA-256 plus CRC-checked members."""
    receipt = inspect_original_zip(path, release)
    try:
        with path.open('rb') as original:
            digest = hashlib.sha256()
            while block := original.read(CHUNK):
                digest.update(block)
            if digest.hexdigest() != receipt['independently_computed_original_zip_sha256']:
                raise OriginalZipError('source ZIP changed since original source integrity gate')
            original.seek(0)
            with zipfile.ZipFile(original) as archive:
                members = member_digests(archive)
    except (OSError, zipfile.BadZipFile) as exc:
        raise OriginalZipError('source ZIP unavailable or corrupted after integrity gate') from exc
    return receipt, members


def compare_original_archives(path_2018: Path, path_2026: Path) -> dict:
    early_receipt, early_members = fingerprint_original(path_2018, '2018')
    late_receipt, late_members = fingerprint_original(path_2026, '2026')
    result = compare_digest_inventories(early_members, late_members)
    result['original_zip_sha256_receipts'] = [
        {'release': '2018', 'sha256': early_receipt['independently_computed_original_zip_sha256']},
        {'release': '2026', 'sha256': late_receipt['independently_computed_original_zip_sha256']},
    ]
    result['original_member_digest_receipts'] = [
        {'release': '2018', 'members': list(early_members.values())},
        {'release': '2026', 'members': list(late_members.values())},
    ]
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--2018-zip', type=Path, required=True)
    p.add_argument('--2026-zip', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        output = compare_original_archives(vars(args)['2018_zip'], vars(args)['2026_zip'])
    except (OriginalZipError, OSError) as exc:
        p.error(str(exc))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
