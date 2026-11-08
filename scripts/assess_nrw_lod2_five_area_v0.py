# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Five fixed NRW LoD2 study-area CityJSON QA receipts; never a statewide estimate.

Manual live mode makes exactly five bounded provider requests and emits aggregate
metadata only. Do not store original CityJSON in Git, logs or public artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

if __package__:
    from .assess_nrw_lod2_cityjson_sample_v0 import (
        MAX_BYTES, ROOF_FIELDS, SampleError, _NoRedirects, assess,
    )
    from .nrw_lod2_roof_code_gate_v0 import RoofCodeError, audit_cityjson_roof_codes
else:
    from assess_nrw_lod2_cityjson_sample_v0 import (
        MAX_BYTES, ROOF_FIELDS, SampleError, _NoRedirects, assess,
    )
    from nrw_lod2_roof_code_gate_v0 import RoofCodeError, audit_cityjson_roof_codes


@dataclass(frozen=True)
class StudyArea:
    code: str
    description: str
    bbox: tuple[float, float, float, float]

    @property
    def url(self) -> str:
        return (
            "https://ogc-api.nrw.de/3dg/v1/collections/building/items?"
            "f=cityjson&limit=5&bbox="
            + ",".join(f"{v:.4f}" for v in self.bbox)
        )


# Convenience places selected in advance; nonprobabilistic and not population representative.
AREAS: tuple[StudyArea, ...] = (
    StudyArea("koeln", "Koeln urban core", (6.9500, 50.9300, 6.9520, 50.9320)),
    StudyArea("muenster", "Muenster urban centre", (7.6250, 51.9600, 7.6290, 51.9640)),
    StudyArea("dortmund", "Dortmund Ruhr urban core", (7.4610, 51.5120, 7.4650, 51.5160)),
    StudyArea("schleiden", "Schleiden Eifel small-town window", (6.4740, 50.5290, 6.4800, 50.5340)),
    StudyArea("meschede", "Meschede Sauerland small-town window", (8.2770, 51.3480, 8.2830, 51.3530)),
)
assert len(AREAS) == len({area.code for area in AREAS}) == 5


def fetch_fixed_area(area: StudyArea) -> tuple[bytes, str]:
    """One GET, no redirect or retry, bounded response and fixed allowlisted host."""
    if area not in AREAS:
        raise SampleError("area not on immutable study allowlist")
    request = Request(
        area.url,
        headers={
            "Accept": "application/city+json",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-NRW-five-area-research/0",
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirects()).open(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != area.url:
                raise SampleError("unexpected response status or effective URL")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SampleError("compressed original sample not supported")
            size_value = response.headers.get("Content-Length")
            if size_value is not None:
                try:
                    size = int(size_value)
                except ValueError as exc:
                    raise SampleError("malformed Content-Length") from exc
                if size <= 0 or size > MAX_BYTES:
                    raise SampleError("declared response exceeds size budget")
            return response.read(MAX_BYTES + 1), response.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SampleError(f"fixed area acquisition failed: {type(exc).__name__}") from exc


def summarize(
    observations: list[tuple[StudyArea, bytes, str]],
) -> dict:
    """Validate all five separately and aggregate counts without source entities."""
    if len(observations) != len(AREAS):
        raise SampleError("exactly five planned area responses required")
    if set(area for area, _, _ in observations) != set(AREAS):
        raise SampleError("duplicate, missing or unapproved area")
    by_area: dict[str, dict] = {}
    for area, raw, media in observations:
        # Each sample's geometry must intersect its *own* declared bbox,
        # not the Cologne bbox used by the original single-area checker.
        receipt = assess(raw, bbox=area.bbox, source_url=area.url, media_type=media)
        try:
            roof = audit_cityjson_roof_codes(raw)
        except RoofCodeError as exc:
            raise SampleError(f"official roof code audit blocked: {area.code}: {exc}") from exc
        if roof["root_buildings"] != receipt["buildings"] or roof["building_parts"] != receipt["building_parts"]:
            raise SampleError("inconsistent building/part counting across independent gates")
        receipt["roof_code_audit"] = roof
        by_area[area.code] = receipt
    ordered = [
        {"area_code": area.code, "description": area.description, **by_area[area.code]}
        for area in AREAS
    ]
    total_buildings = sum(r["buildings"] for r in ordered)
    total_parts = sum(r["building_parts"] for r in ordered)
    if not total_buildings:
        raise SampleError("no original Buildings found")
    root_roof_codes: Counter[str] = Counter()
    part_roof_codes: Counter[str] = Counter()
    for item in ordered:
        audit = item["roof_code_audit"]
        root_roof_codes.update(audit["root_roof_code_counts"])
        part_roof_codes.update(audit["part_roof_code_counts"])
    return {
        "profile": "oc-nrw-lod2-five-convenience-area-audit-v0",
        "sample_selection": "fixed_nonprobability_convenience_windows_not_statewide_representative",
        "areas_attempted": len(AREAS),
        "total_root_buildings": total_buildings,
        "total_building_parts": total_parts,
        "root_roof_code_counts": dict(sorted(root_roof_codes.items())),
        "part_roof_code_counts": dict(sorted(part_roof_codes.items())),
        "root_specific_roof_form": sum(item["roof_code_audit"]["root_specific_roof_form"] for item in ordered),
        "root_mixed_or_other_roof_form": sum(item["roof_code_audit"]["root_mixed_or_other_roof_form"] for item in ordered),
        "root_missing_roof_form": sum(item["roof_code_audit"]["root_missing_roof_form"] for item in ordered),
        "roots_with_multiple_part_roof_codes": sum(item["roof_code_audit"]["roots_with_multiple_part_roof_codes"] for item in ordered),
        "total_vertices": sum(r["vertices"] for r in ordered),
        "root_attribute_present": {
            field: sum(r["root_attribute_present"][field] for r in ordered)
            for field in ROOF_FIELDS
        },
        "part_attribute_present": {
            field: sum(r["part_attribute_present"][field] for r in ordered)
            for field in ROOF_FIELDS
        },
        "root_missing_with_part_attribute": {
            field: sum(r["root_missing_with_part_attribute"][field] for r in ordered)
            for field in ROOF_FIELDS
        },
        "areas": ordered,
        "original_feature_rows_embedded": False,
        "independent_insurer_exposure": False,
        "source_scientifically_admitted": False,
        "model_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--live", action="store_true", help="Exactly five bounded original source GETs")
    modes.add_argument(
        "--offline-dir", type=Path,
        help="Directory of five local synthetic CityJSON fixtures, one per area.code; never in Git",
    )
    modes.add_argument("--plan", action="store_true", help="Print fixed endpoints without network or data")
    args = parser.parse_args(argv)
    if args.plan:
        print(json.dumps(
            [{"code": area.code, "url": area.url} for area in AREAS],
            sort_keys=True,
        ))
        return 0
    observations: list[tuple[StudyArea, bytes, str]] = []
    try:
        for area in AREAS:
            if args.live:
                raw, media = fetch_fixed_area(area)
            else:
                file = args.offline_dir / f"{area.code}.json"
                if file.stat().st_size > MAX_BYTES:
                    raise SampleError(f"oversized offline sample: {area.code}")
                raw, media = file.read_bytes(), "application/city+json"
            observations.append((area, raw, media))
        result = summarize(observations)
        result["transport_verified_by_script"] = args.live
        result["checked_utc"] = datetime.now(timezone.utc).isoformat()
    except (SampleError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
