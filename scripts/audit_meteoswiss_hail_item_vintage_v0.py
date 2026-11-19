# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline scientific time-identity guard for *metadata-only* MeteoSwiss hail Items.

The STAC Item datetime is searchable/nominal metadata, not evidence of the
underlying NetCDF measurement month. This guard never returns an accepted
observation month, even if the Item id/title/nominal datetime agree. MeteoSwiss
calculates hail climate products for April--September; an October Item is not
proof of zero hail or an October hail observation. No network or asset reads.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import Any

COLLECTION_ID = "ch.meteoschweiz.ogd-radar-derived-grid"
SOURCE_ID = "meteoswiss.national-hail-climatology"
_ITEM = re.compile(r"^(20\d{2})(0[1-9]|1[0-2])-ch$")
_TITLE = re.compile(r"^CH at (0[1-9]|1[0-2])\.(20\d{2})$")
_UTC = re.compile(r"^20\d{2}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|\+00:00)$")


class HailVintageError(ValueError):
    """Unparseable or wrongly scoped source-metadata research row."""


def screen_item_vintage(record: Any) -> dict[str, Any]:
    """Classify a bounded normalized metadata excerpt; never admit source values.

    The record follows the existing research.source_sample_v0.sample_json keys,
    not full provider JSON. The original response hashes belong to separate
    provenance records; no transport or source-byte verification occurs here.
    """
    if type(record) is not dict or record.get("exact_collection") != COLLECTION_ID:
        raise HailVintageError("wrong source Collection or research record")
    item_id, title, stamp = (record.get("item_id"), record.get("item_title_observed"),
                             record.get("item_datetime_observed"))
    if any(type(x) is not str for x in (item_id, title, stamp)):
        raise HailVintageError("item id, title and nominal time required")
    match_id, match_title = _ITEM.fullmatch(item_id), _TITLE.fullmatch(title)
    if match_id is None or match_title is None:
        raise HailVintageError("unsupported item id/title grammar")
    if not _UTC.fullmatch(stamp):
        raise HailVintageError("nominal Item timestamp must be explicit RFC3339 UTC")
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HailVintageError("invalid Item datetime") from exc
    if dt.utcoffset() != timedelta(0):
        raise HailVintageError("non-UTC nominal Item timestamp")
    item_year, item_month = int(match_id[1]), int(match_id[2])
    title_month, title_year = int(match_title[1]), int(match_title[2])
    title_matches = (item_year, item_month) == (title_year, title_month)
    nominal_matches = (item_year, item_month) == (dt.year, dt.month)
    season = 4 <= item_month <= 9
    blockers = []
    if not title_matches:
        blockers.append("title_item_month_mismatch")
    if not nominal_matches:
        blockers.append("nominal_datetime_item_month_mismatch")
    if not season:
        blockers.append("outside_april_september_hail_computation_season")
    blockers.append("source_asset_product_time_and_values_not_verified")
    return {
        "source_id": SOURCE_ID,
        "collection_id": COLLECTION_ID,
        "item_id": item_id,
        "item_year_month": f"{item_year:04d}-{item_month:02d}",
        "title_matches_item_month": title_matches,
        "nominal_datetime_matches_item_month": nominal_matches,
        "item_month_in_hail_season": season,
        "blockers": blockers,
        "verified_asset_observation_month": None,
        "original_asset_bytes_examined": 0,
        "independent_hail_observation_verified": False,
        "model_input_approved": False,
    }
