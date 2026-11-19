# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Cuxhaven 2 station-7 view of the shared offline PSMSL RLR monthly preflight.

Only independently authorized local input bytes are screened. Station identity,
origin, rights, datum validity and CAT admission are not independently proven.
Official station: https://psmsl.org/data/obtaining/stations/7.php
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.audit_psmsl_rlr_monthly_v0 import MAX_BYTES, audit_bytes

MAX_ORIGINAL_BYTES = MAX_BYTES  # Kept for existing callers.
_STATION_ID = 7


def screen_original_bytes(original: bytes | bytearray) -> dict[str, object]:
    """Validate bytes supplied by the caller; preserve historical output keys."""
    if not isinstance(original, (bytes, bytearray)):
        raise ValueError('expected local bytes, not an unverified URL or decoded object')
    result = audit_bytes(bytes(original), station_id=_STATION_ID)
    return {
        'source_id': result['source_id'],
        'product': 'PSMSL CUXHAVEN 2 RLR monthly',
        'station_id': _STATION_ID,
        'station_id_claimed': result['station_id_claimed'],
        # Backward-compatible aliases: these are input-byte hashes, not
        # independent provider-origin verification.
        'original_sha256': result['input_sha256'],
        'original_bytes': result['input_bytes'],
        'input_sha256': result['input_sha256'],
        'input_bytes': result['input_bytes'],
        'rows': result['calendar_month_count'],
        'first_month': result['first_month'],
        'last_month': result['last_month'],
        'missing_months': result['missing_monthly_means'],
        'interpolated_months': result['interpolated_months'],
        'flagged_months': result['flagged_months'],
        'caution_flag_months': result['caution_flag_months'],
        'mean_tidal_level_flag_months': result['mean_tidal_level_flag_months'],
        'provider_origin_verified': result['provider_origin_verified'],
        'source_rights_and_service_automation': 'not_verified_for_this_sample',
        'station_datum_review': 'required: historic MTL to MSL (-88 mm before 1984) already applied to PSMSL RLR; do not apply again',
        'cat_model_admission': 'not_admitted',
        'neon_storage': 'storage_not_verified',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_file', type=Path, help='already-authorized local station-7 RLR monthly bytes')
    args = parser.parse_args()
    try:
        with args.original_file.open('rb') as stream:
            original = stream.read(MAX_ORIGINAL_BYTES + 1)
        result = screen_original_bytes(original)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
