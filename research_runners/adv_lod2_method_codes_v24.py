# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""AdV PQS 3D-Gebaeudemodelle v2.4 (2023-03-23) candidate code membership.

Annex 1 section 2.13.4, printed pages 11-12. Historical Berlin 2022
method-code equivalence is not proven: no production interpretation.
"""
from __future__ import annotations

import re
from typing import Any

VERSION="AdV-PQS-3D-Geabudemodelle-2.4"
VERSION_DATE="2023-03-23"
HISTORIC_BERLIN_SOURCE_YEAR=2022
REFERENCE_URL=("https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/"
               "deu/lod1-de_produktstandard%20_fuer_3d-gebaeudemodelle.pdf")
CANDIDATES={
    "quelledachhoehe":frozenset(("1000","2000","3000","4000","5000","6000","7000")),
    "quellelage":frozenset(("1000","2000","3000")),
    "quellebodenhoehe":frozenset(("1000","1100","1200","1300","1400","2000","3000","4000")),
}
BUCKETS=("ad_v24_candidate","unlisted_or_malformed","missing")


def _code(value:Any)->str|None:
    if type(value) is int:
        word=str(value)
    elif type(value) is str:
        word=value.strip()
    else:
        return None
    return word if re.fullmatch(r"[0-9]{4}",word) else None


def candidate_membership_counts(records:list[dict])->dict[str,dict[str,int]]:
    """Aggregate code-list membership only: no source value, label, ID or hash."""
    counts={field:{k:0 for k in BUCKETS} for field in CANDIDATES}
    for properties in records:
        if type(properties) is not dict:
            raise ValueError("source record must be a dictionary")
        for field,known in CANDIDATES.items():
            value=properties.get(field)
            if value is None or (type(value) is str and not value.strip()):
                bucket="missing"
            elif _code(value) in known:
                bucket="ad_v24_candidate"
            else:
                bucket="unlisted_or_malformed"
            counts[field][bucket]+=1
    return counts
