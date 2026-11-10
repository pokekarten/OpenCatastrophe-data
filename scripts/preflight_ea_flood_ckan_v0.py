# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed preflight for five fixed Environment Agency CKAN catalogues.

Pass an independently saved JSON response. This program makes no network calls,
never dereferences provider resource links, and does not certify source rights,
original-byte authenticity, flood-depth values or model readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

MAX_BYTES = 262_144
HOST = "https://environment.data.gov.uk"
# (resource UUID, published resource title, CKAN format, resource role)
PACKAGES = {
    "river_present": {
        "id": "e4698ae1-184b-4b5d-801a-90364a93e229",
        "slug": "rivers-and-sea-defended-and-undefended-flood-risk-depths-present-day",
        "modified": "2026-10-30T14:00:39.007132",
        "file_set": "6bf96b5d-1e0b-4c0f-b9f1-a491bdc7dbf5",
        "explore": "f8961d6d-3e0a-4aaa-8e69-e834b85992a3",
        "spatial": "rivers-and-sea-defended-and-undefended-flood-risk-depths-present-day",
        "resources": (
            ("8feddea6-fb5a-4e72-89aa-c2fab208533e", "Rivers_and_Sea_Defended_and_Undefended_Depths_Product_Description.pdf", "PDF", "file"),
            ("99a46480-ba57-4f63-a93b-8b79280de143", "Rivers_and_Sea_defended_and_undefended_flood_risk_depths_present_day.gdb.zip", "ZIP", "file"),
            ("e335140d-00d1-47d2-b11f-8474d0f90dea", "Rivers_and_Sea_defended_and_undefended_flood_risk_depths_present_day.geojson.zip", "ZIP", "file"),
            ("deb4eaed-0d39-422f-8a01-214b18f6e365", "Rivers_and_Sea_Depths.lyrx", "", "file"),
            ("d6a4f925-71e2-42bc-914a-e76a45437fa1", "Rivers_1in100_Sea_1in200_defended_depths_Download", "", "explore"),
            ("050ce809-585d-44ce-b1ca-5d9a06b8e2d8", "Rivers_1in100_Sea_1in200_defended_depths_WMS", "", "wms"),
            ("7095d735-bfcd-43b1-8ed4-6061a24cedb5", "Rivers_1in100_Sea_1in200_defended_depths_WFS", "", "wfs"),
            ("58e3fb53-9756-481a-9a5d-06c838c1dad1", "OGC API - Features service", "", "ogc"),
        ),
    },
    "river_climate": {
        "id": "67a734bb-2b7b-491a-aafd-3f7e52c8d7f3",
        "slug": "rivers-and-sea-defended-and-undefended-flood-risk-depths-climate-change",
        "modified": "2026-10-30T14:00:37.670274",
        "file_set": "2ebb2fe0-06a3-45a2-a366-f3124668682c",
        "explore": "4c61ac42-ab7c-46f7-b84c-f9a2f78c267d",
        "spatial": "rivers-and-sea-defended-and-undefended-flood-risk-depths-climate-change",
        "resources": (
            ("e1d9e56a-fc93-4419-9d32-df5cadf742e7", "Rivers_and_Sea_Climate_Change_Depths.lyrx", "", "file"),
            ("e468d35a-d14f-4ccf-bd70-5ea78cb6aed8", "Rivers_and_Sea_Defended_and_Undefended_Depths_Product_Description.pdf", "PDF", "file"),
            ("6ab5c4df-0c28-490b-a47c-01e95c1aa807", "Rivers_and_Sea_defended_and_undefended_flood_risk_depths_climate_change.gdb.zip", "ZIP", "file"),
            ("38349b03-8d94-4e27-8f82-c363d421d43a", "Rivers_and_Sea_defended_and_undefended_flood_risk_depths_climate_change.geojson.zip", "ZIP", "file"),
            ("5365cba9-29b3-4c1a-9fc8-da878baffaac", "Rivers_1in100_Sea_1in200_defended_depths_CCP1_Download", "", "explore"),
            ("31432449-95b5-4367-b986-d2374c4c1658", "Rivers_1in100_Sea_1in200_defended_depths_CCP1_WMS", "", "wms"),
            ("d6cb7d62-4b25-4ca5-8bbd-40920b5a8056", "Rivers_1in100_Sea_1in200_defended_depths_CCP1_WFS", "", "wfs"),
            ("13231be9-938a-4559-8bbb-3a55481a5cbd", "OGC API - Features service", "", "ogc"),
        ),
    },
    "surface_present": {
        "id": "b0bbfacf-ccf7-4ed9-a94c-be18d91c258d",
        "slug": "flood-map-for-planning-surface-water-spatial-planning-depths-present-day",
        "modified": "2026-07-06T07:10:48.657123",
        "file_set": "19c68664-4516-4436-93c8-e2037d77c1d1",
        "explore": "fa3a36ed-121c-424b-b8bf-8108f959b7a9",
        "spatial": "fmfp-surface-water-depths",
        "resources": (
            ("84d4235b-a2ad-4b08-a45d-b12fd11389cc", "Surface Water Spatial Planning Product Description.pdf", "PDF", "file"),
            ("3f8c6896-7c50-4325-a778-cd870a74615b", "Surface_Water_Spatial_Planning_Depths.lyrx", "", "file"),
            ("61cb7972-15ec-45ef-8841-16a8522f14f5", "SurfaceWaterSpatialPlanningDepths_Download", "", "explore"),
            ("12236b59-a563-4b31-b26f-04032960b8d0", "SurfaceWaterSpatialPlanningDepths_WMS", "", "wms"),
        ),
    },
    "river_3p3_present": {
        "id": "2b1dc7a4-ff9f-42fd-9971-11638eabf814",
        "slug": "rivers-and-sea-3-3-defended-flood-risk-depths-present-day",
        "modified": "2026-10-30T14:00:33.438078",
        "file_set": "54d9e4b8-2778-4ed0-b6dc-ddc385386fce",
        "explore": "767c96e6-b149-4744-9d4d-34b32f6c0e1b",
        "spatial": "rivers-and-sea-1in30-defended-flood-risk-depths-present-day",
        "resources": (
            ("80478751-19e7-4928-bb48-af6379511c77", "Rivers_and_Sea_3_3_defended_flood_risk_depths_present_day.gdb.zip", "ZIP", "file"),
            ("e405ef64-314f-4121-aefd-62aa2e2cb04e", "Rivers_and_Sea_3_3_defended_flood_risk_depths_present_day.geojson.zip", "ZIP", "file"),
            ("4bd8350b-18ff-44f9-94d3-f4c8324437ae", "Rivers_and_Sea_3_3_defended_flood_risk_depths_present_day.gpkg.zip", "ZIP", "file"),
            ("a45be695-8cfa-4473-a0a1-a944daa0ca60", "Rivers_and_Sea_Defended_and_Undefended_Depths_Product_Description.pdf", "PDF", "file"),
            ("e705cdeb-9bb5-4f01-a54c-62c8c62e7c17", "Rivers_and_Sea_Depths.lyrx", "", "file"),
            ("eea725c8-6972-4119-986c-26f4d3a1491f", "Rivers_1in30_Sea_1in30_defended_depths_Download", "", "explore"),
            ("fc2a5564-dc3f-4821-b525-12aeddb2a968", "Rivers_1in30_Sea_1in30_defended_depths_WMS", "", "wms"),
            ("6d2191d1-5664-4ea9-9ace-07f2e2637753", "Rivers_1in30_Sea_1in30_defended_depths_WFS", "", "wfs"),
            ("eab4f02c-b2eb-45d0-a8e5-d12b8467fe63", "OGC API - Features service", "", "ogc"),
        ),
    },
    "river_3p3_climate": {
        "id": "9d5e56d5-7713-42a1-890f-3d0a3e895cd5",
        "slug": "rivers-and-sea-3-3-defended-flood-risk-depths-climate-change",
        "modified": "2026-10-30T14:00:32.171469",
        "file_set": "7844932f-d689-471c-aa1e-76ee0cbd51ef",
        "explore": "defaf0fb-8574-46c6-bb2e-e6eb1a5e467a",
        "spatial": "rivers-and-sea-1in30-defended-flood-risk-depths-climate-change",
        "resources": (
            ("2e1dca94-fcda-48e4-aa1b-dbac16f45978", "Rivers_and_Sea_3_3_defended_flood_risk_depths_climate_change.gdb.zip", "ZIP", "file"),
            ("06b5dbee-d911-46c6-affd-55622c925f47", "Rivers_and_Sea_3_3_defended_flood_risk_depths_climate_change.geojson.zip", "ZIP", "file"),
            ("dfa5eb9e-3ffa-480e-9416-836b138d24be", "Rivers_and_Sea_3_3_defended_flood_risk_depths_climate_change.gpkg.zip", "ZIP", "file"),
            ("706ed33e-1b2b-4b78-ba0b-238d179586ee", "Rivers_and_Sea_Climate_Change_Depths.lyrx", "", "file"),
            ("06a37b85-3d8b-4422-a93c-d055b456ef05", "Rivers_and_Sea_Defended_and_Undefended_Depths_Product_Description.pdf", "PDF", "file"),
            ("950f383d-a11a-40b4-bf4e-b2e213d33ee7", "Rivers_1in30_Sea_1in30_defended_depths_CCP1_Download", "", "explore"),
            ("7d8d09be-efc9-4139-8579-b40916353e07", "Rivers_1in30_Sea_1in30_defended_depths_CCP1_WMS", "", "wms"),
            ("1983e819-f26e-4dc3-8282-fb60a490d9e0", "Rivers_1in30_Sea_1in30_defended_depths_CCP1_WFS", "", "wfs"),
            ("1e1ef0ba-c120-45a8-b7a8-72ce83bcba7d", "OGC API - Features service", "", "ogc"),
        ),
    },
}


# Original response-body receipts: raw bytes were retrieved from the official CKAN
# publisher via a third-party HTTP transport on 2026-11-10. These hashes enable
# exact-byte comparison, NOT proof that future caller-supplied bytes are authentic.
# No provider response body, catalogue row values, or resource asset bytes are
# stored in this repository.
OBSERVED_ORIGINAL_METADATA_RECEIPTS = {
    "river_present": (13469, "943bed40c29050164ac059f5ae8335761bf38ee70b44bfbd233b7b31f31212e7"),
    "river_climate": (14594, "385b691407fa761cbf0179f0f78e274f17faa7a1f7a49241ae6be0d9c7614f33"),
    "surface_present": (9555, "4c79f4f6df2530f92118269090cf66ec13dbab6468d59166622c7c7d19aff458"),
    "river_3p3_present": (13959, "64d01c89e24c82e7c9384f1a8a2762ddc065890bbbff81e19e16bc4fc8a32857"),
    "river_3p3_climate": (15093, "15ba47630e376659d3c22dcdcd72ac504e3ee5ff8b150b0491e5613848e3e1fa"),
}


class EACatalogueError(ValueError):
    """Missing, changed or unsafe publisher metadata."""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EACatalogueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise EACatalogueError("non-finite JSON value")


def expected_url(package: dict[str, Any], name: str, role: str) -> str:
    """Expected catalogue metadata link; never execute or return this URL."""
    if role == "file":
        return f"{HOST}/api/file/download?fileDataSetId={package['file_set']}&fileName={name}"
    if role == "explore":
        return f"{HOST}/explore/{package['explore']}?download=true"
    if role == "ogc":
        return f"{HOST}/spatialdata/{package['spatial']}/ogc/features/v1"
    if role in {"wms", "wfs"}:
        return f"{HOST}/spatialdata/{package['spatial']}/{role}"
    raise EACatalogueError("unknown resource role")


def inspect_metadata(raw: bytes, dataset: str) -> dict[str, Any]:
    if dataset not in PACKAGES:
        raise EACatalogueError("unrecognised fixed dataset selector")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise EACatalogueError("unbounded or empty JSON response")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EACatalogueError("invalid UTF-8 JSON") from exc
    if type(doc) is not dict or doc.get("success") is not True:
        raise EACatalogueError("CKAN success=true expected")
    obj = doc.get("result")
    package = PACKAGES[dataset]
    if type(obj) is not dict or any((
        obj.get("id") != package["id"],
        obj.get("name") != package["slug"],
        obj.get("metadata_modified") != package["modified"],
        obj.get("private") is not False,
    )):
        raise EACatalogueError("package identity, version or public catalogue status drift")
    # CKAN isopen=false and licence_id=null appear in the official records;
    # neither flag can establish asset access rights. Only observe licence label.
    extras = obj.get("extras")
    if type(extras) is not list:
        raise EACatalogueError("publisher licence metadata missing")
    labels = [x.get("value") for x in extras if type(x) is dict and x.get("key") == "licence"]
    if labels != ['["Open Government Licence"]']:
        raise EACatalogueError("published licence label changed or duplicated")
    resources = obj.get("resources")
    frozen = {rid: (name, fmt, role) for rid, name, fmt, role in package["resources"]}
    if type(resources) is not list or len(resources) != len(frozen) or obj.get("num_resources") != len(frozen):
        raise EACatalogueError("resource inventory count changed")
    seen: set[str] = set()
    for item in resources:
        if type(item) is not dict or type(item.get("id")) is not str:
            raise EACatalogueError("malformed CKAN resource")
        rid = item["id"]
        if rid in seen or rid not in frozen:
            raise EACatalogueError("unknown or repeated resource identity")
        seen.add(rid)
        name, fmt, role = frozen[rid]
        if item.get("name") != name or item.get("format") != fmt or item.get("url") != expected_url(package, name, role):
            raise EACatalogueError("resource name, format or exact publisher URL drift")
    digest = hashlib.sha256(raw).hexdigest()
    observed_length, observed_digest = OBSERVED_ORIGINAL_METADATA_RECEIPTS[dataset]
    return {
        "contract": "EA-FLOOD-CKAN-METADATA-PREFLIGHT-v0",
        "dataset_selector": dataset,
        "dataset_id": package["id"],
        "metadata_modified": package["modified"],
        "catalogue_license_label": "Open Government Licence (unreviewed)",
        "resource_count": len(seen),
        "resource_roles": dict(sorted(Counter(row[3] for row in package["resources"]).items())),
        "input_bytes": len(raw),
        "input_sha256": digest,
        "matches_observed_original_metadata_receipt": (
            len(raw) == observed_length and digest == observed_digest
        ),
        "observed_original_metadata_receipt_date": "2026-11-10",
        "input_authenticity_verified": False,
        "provider_requests_performed": 0,
        "resource_links_followed": 0,
        "building_depth_observations_read": 0,
        "commercial_reuse_approved": False,
        "model_data_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dataset", choices=tuple(PACKAGES), required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        result = inspect_metadata(raw, args.dataset)
    except (OSError, EACatalogueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
