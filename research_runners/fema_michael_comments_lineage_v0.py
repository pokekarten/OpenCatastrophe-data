# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded FEMA Hurricane Michael imagery-provenance hint counts.

Strictly *aggregate* count-only where-conditions. Never request COMMENTS
values, object IDs, points, personally identifying property fields or images.
A keyword-negative comment count does not demonstrate absence of upstream
image use; the source permits null/other comments.
"""

from __future__ import annotations

from typing import Any

SOURCE_COHORT = "DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'"
SOURCE_COUNT = 23682
TOKENS = (
    "NOAA", "NICB", "NCIB", "GIC", "VEXCEL", "IMAGE", "IMAGERY",
    "AERIAL", "ORTHO", "2018", "DATE", "SATELLITE", "FLIGHT",
    "GOOGLE", "FEMA",
)
SOURCE_LAYER_QUERY = (
    "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
    "FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0/query"
)


class CommentsLineageError(ValueError):
    """Missing, untrusted or inconsistent provider-style aggregate evidence."""


def original_query_plan() -> dict[str, dict[str, str]]:
    """Build exact 18 count-only FEMA requests with no comment field return."""
    where = {
        "COMMENTS_non_null": SOURCE_COHORT + " AND COMMENTS IS NOT NULL",
        "IMG_DATE_non_null": SOURCE_COHORT + " AND IMG_DATE IS NOT NULL",
        "PROD_DATE_non_null": SOURCE_COHORT + " AND PROD_DATE IS NOT NULL",
    }
    for word in TOKENS:
        where["COMMENTS_token_" + word] = (
            SOURCE_COHORT + " AND COMMENTS LIKE '%" + word + "%'"
        )
    return {
        key: {
            "where": clause,
            "returnCountOnly": "true",
            "returnGeometry": "false",
            "f": "json",
        }
        for key, clause in where.items()
    }


def _count(reply: Any) -> int:
    if type(reply) is not dict or set(reply) != {"count"}:
        raise CommentsLineageError("one strictly aggregate count-only reply required")
    n = reply["count"]
    if type(n) is not int or not 0 <= n <= SOURCE_COUNT:
        raise CommentsLineageError("count exceeds frozen exact source cohort")
    return n


def reconcile_lineage_counts(responses: Any) -> dict[str, Any]:
    """Check non-null and token hits, but never expose the comments themselves."""
    if type(responses) is not dict or set(responses) != set(original_query_plan()):
        raise CommentsLineageError("all frozen exact FEMA query receipts required")
    counts = {k: _count(v) for k, v in responses.items()}
    nonnull = counts["COMMENTS_non_null"]
    for token in TOKENS:
        if counts["COMMENTS_token_" + token] > nonnull:
            raise CommentsLineageError("keyword hits exceed non-null COMMENTS source count")
    return {
        "profile": "fema_michael_2018_aggregated_image_provenance_comments_v0",
        "source_disaster": "DR-4399",
        "source_method": "RS",
        "source_damage_type": "WI",
        "frozen_source_cohort_count": SOURCE_COUNT,
        "comment_field_nonnull_count": nonnull,
        "imagery_date_nonnull_count": counts["IMG_DATE_non_null"],
        "production_date_nonnull_count": counts["PROD_DATE_non_null"],
        "image_lineage_keyword_counts": {
            word: counts["COMMENTS_token_" + word] for word in TOKENS
        },
        "per_feature_comments_requested_or_returned": False,
        "missing_image_date_imputed_from_event": False,
        "original_assessment_image_identified": False,
        "independent_damage_labels_proven": False,
        "model_input_admitted": False,
    }
