<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAL FIRE DINS aggregate inspection QA v0 — no insurance-loss inference

This research helper is a narrow follow-up to
`docs/research/calfire-dins-scientific-interface-20261101.md` and the
non-admission candidate `us.calfire.dins.structure-damage`.

## Why

The official public DINS dataset is advertised under Creative Commons
Attribution and with no generic public-use restriction:
<https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>.
The portal was last updated on 2026-10-21 and offers CSV, GeoJSON, GPKG,
and ArcGIS REST formats. That public licence **does not itself validate**
this exact API's automation policy, any private-address release, or scientific
fitness for insurance pricing. The existing contract stays
`documented_only` with no authorized network probe.

The source documents that non-damaged inspections start in 2018; a separate
incident can still have access-related inspection gaps. Sampling of the
wildfire impact zone is not a complete independent count of exposed buildings.
Damage categories are **ordinal inspection descriptions**, not a financial
claim severity scale.

## Bounded implementation

`scripts/calfire_dins_aggregate_qc_v0.py` accepts one offline JSON
aggregation of DINS damage class **counts only**, already prepared in a
separately authorized environment, or wholly invented synthetic input. It
does not accept feature rows, exact addresses, names, polygons, point
coordinates, parcel keys, policy records, insured values, or loss ratios.
No URL parameters, API calls, remote requests, source downloads or
redistribution steps are implemented.

A fixed six-class taxonomy and exact input schema are required. Missing,
negative, boolean, unknown or fractional counts and unrecognized frame
identities are rejected. Source years begin at 2013; before 2018 the
`No Damage` cohort is not an eligible recorded control group. All outputs
explicitly mark **selection bias unresolved**, **exposed-population
denominator unavailable**, **no vulnerability probability inferred**,
**no financial loss inferred**, and **not admitted as model data**.

For external aggregates a syntactically valid 64-character lower-case
source SHA-256 field is mandatory, but this helper **cannot attest** that
the hash matches a real provider download or that rights were cleared.
Its output says so. Source evidence remains a separate admission gate.

The helper emits all six counts only if the inspected count is at least
10 **and every nonzero class count is at least 10**. Otherwise the entire
count distribution and total are omitted. This is a conservative
small-cell **suppression heuristic**, **not formal disclosure control**:
it does not eliminate cross-query differencing, reidentification or
source-specific privacy assessment. Never repeatedly publish overlapping
cohorts without independent disclosure-control review.

## Synthetic-only example

A synthetic input with `event_year=2022`, `origin=synthetic`,
`source_snapshot_sha256=null`, `contains_feature_rows=false`,
`inspection_frame=calfire_dins_inspected_structures` and all six
published provider damage class counts equal to 10 passes inspection.
The output reports 60 *inspected records in that synthetic cohort*, **not**
60 exposed insured buildings or 60 financial loss observations.

## Tests and evidence boundary

`tests/test_calfire_dins_aggregate_qc_v0.py` contains 20 offline
synthetic tests: verified schema, historic 2013/2017/2018 break, full-table
small-cell suppression, null/invalid source SHA semantics, boolean and
negative/fractional count traps, extra address fields, duplicate JSON keys,
zero total, and raw-feature-payload rejection.

**Next scientific milestone:** a reviewed per-incident external exposure
denominator, aligned spatial/temporal footprint and selection mechanism;
then compare conditional inspected damage states to a separate model challenge
dataset. Neither an inspection histogram nor the building valuation field is
an unconditional insurance vulnerability curve.
