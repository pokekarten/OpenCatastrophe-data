# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative temporal coverage check using explicit half-open intervals."""
from datetime import datetime


def assess(hazard_start, hazard_end_exclusive, loss_start, loss_end_exclusive,
           geographic_coverage_verified=False):
    # A non-empty string such as "false" is truthy in Python and must never
    # constitute scientific evidence that geographic coverage was checked.
    if type(geographic_coverage_verified) is not bool:
        raise ValueError("geographic_coverage_verified must be a boolean")
    hs,he,ls,le=map(datetime.fromisoformat,
                   [hazard_start,hazard_end_exclusive,loss_start,loss_end_exclusive])
    if any(t.tzinfo is None for t in [hs,he,ls,le]):
        raise ValueError('Explicit timezone required')
    if he<=hs or le<=ls:
        raise ValueError('Nonpositive interval')
    temporal=hs<=ls and he>=le
    return {'hazard_covers_loss_interval':temporal,
            'uncovered_start_hours':max(0,(hs-ls).total_seconds()/3600),
            'uncovered_end_hours':max(0,(le-he).total_seconds()/3600),
            'geographic_coverage_verified':geographic_coverage_verified,
            'support_gate_passed':temporal and geographic_coverage_verified,
            'matched_insured_population_verified':False}
