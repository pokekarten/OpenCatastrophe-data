# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent 10k-year exact row receipt for FICTIONAL Neon toy CAT data.

Only reproduces deterministic fabricated hazards, positions and damage.
Does not connect to Neon or admit any real insured portfolio.
"""
from __future__ import annotations

import hashlib

PREFIX = "OC_NEON_10K_SYNTH_GUL_V0"
ASSETS = tuple((f"SYNTH-{i:02d}", 100000 + 25000 * i) for i in range(1, 13))
PERILS = (("windstorm", 26), ("flood", 13))
YEARS = 10000
EXPECTED = {
    "annual_exact_md5": "6aebdda0c542f06a882ec16a4fcaa667",
    "event_exact_md5": "e0b6b2414c0a12459c47785a7de53777",
    "event_asset_exact_md5": "8cba885a6e1aab7d43e2fe1087fe0d95",
    "event_intensity_exact_md5": "2f11da6a6e1fb752cc410f50bfeffbc6",
    "years": 10000, "events": 1541, "asset_event_rows": 18492,
}


def source_hash(s: str) -> bytes:
    return hashlib.md5(s.encode("ascii")).digest()


def compute_receipts(*, assets=ASSETS, synthetic=True, years=YEARS) -> dict:
    if not synthetic or type(assets) is not tuple or assets != ASSETS or years != YEARS:
        raise ValueError("strict synthetic Neon 10k fixture required")
    annual = []
    events = []
    asset_rows = []
    intensity_rows = []
    event_count = 0
    for yr in range(years):
        total_year = 0
        max_event = 0
        count_year = 0
        for peril, threshold in sorted(PERILS):
            h = source_hash(f"{PREFIX}|{yr}|{peril}")
            if h[0] >= threshold:
                continue
            count_year += 1
            event_count += 1
            intensity = 1 + h[1] % 5
            intensity_rows.append(f"{yr}:{peril}:{intensity}")
            event_sum = 0
            for asset_id, value in assets:
                local = source_hash(f"{PREFIX}|local|{yr}|{peril}|{asset_id}")
                susceptibility = 1 + local[2] % 3
                if value * intensity * susceptibility % 100:
                    raise ValueError("fractional GUL not representable in integer EUR")
                loss = value * intensity * susceptibility // 100
                asset_rows.append(f"{yr}:{peril}:{asset_id}:{loss}")
                event_sum += loss
            events.append(f"{yr}:{peril}:{event_sum}")
            total_year += event_sum
            max_event = max(max_event, event_sum)
        annual.append(f"{yr}:{total_year}:{max_event}:{count_year}")
    result = {
        "annual_exact_md5": hashlib.md5("|".join(annual).encode("ascii")).hexdigest(),
        "event_exact_md5": hashlib.md5("|".join(events).encode("ascii")).hexdigest(),
        "event_asset_exact_md5": hashlib.md5("|".join(asset_rows).encode("ascii")).hexdigest(),
        "event_intensity_exact_md5": hashlib.md5("|".join(intensity_rows).encode("ascii")).hexdigest(),
        "years": len(annual),
        "events": event_count,
        "asset_event_rows": len(asset_rows),
    }
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(compute_receipts(), indent=2, sort_keys=True))
