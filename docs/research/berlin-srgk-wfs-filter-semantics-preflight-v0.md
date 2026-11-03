<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin SRGK model-area: original WFS schema and count-only spatial filter preflight

**Research only. No local model coverage or dryness has yet been proven.**

## Original failure

The first original-source [Berlin pilot WFS run 41354987880](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354987880)
requested a model-area feature in the fixed pilot BBOX
(391700, 5819950, 391900, 5820150), EPSG:25833.
The server returned a polygon **without positive-area intersection**
with that pilot. The code correctly blocked any model-area coverage
or absence-of-hazard claim.

A separate [draft #1093](https://github.com/pokekarten/OpenCatastrophe-data/pull/1093)
addresses the *negative original-source receipt* for this failure.
This PR does not change any file on the draft branch.

The [WFS 2.0 reference](https://docs.geoserver.org/main/en/user/services/wfs/reference/)
and [German GDI training](https://gdi-de.github.io/e-learning/wfs/text/operations.html)
describe spatial filtering and axis-order semantics, but cannot
certify behavior of this particular official Berlin WFS.

## New independent original test

The dependency-free script
research_runners/berlin_srgk_wfs_schema_hits_v0.py makes **exactly
three fixed original HTTPS operations** to the official
https://gdi.berlin.de/services/wfs/ua_srgk endpoint:

1. A single WFS 2.0 DescribeFeatureType for the public
   ua_srgk:a_modellgebiete model-area layer, bounded to 512 KiB.
   Only safe public schema field names / possible geometry field
   names are reported; these do not yet prove safe spatial filter use.
2. A count-only GetFeature resultType=hits control for the same
   layer, maximum 16 KiB. Reject any original feature geometry.
3. The same hits-only request with the frozen BLD4 pilot BBOX
   (391700,5819950,391900,5820150,EPSG:25833), maximum 16 KiB.

Requests are fixed URL allowlisted. Non-200, redirects, unknown
media types, invalid or huge XML, DTD/entities, or actual returned
features are **blocked**. The original responses are ephemeral:
only SHA-256, byte counts, optional public attribute names, count-only
numeric metadata and a conservative comparison are recorded.
No original model-area polygons, WFS IDs, addresses, raster cells,
building locations or insurer data are stored.

A zero pilot hits count does **not** establish that no source model area
intersects the pilot, given the independently observed original BBOX
misbehavior. A positive count does **not** prove polygon intersection.
Both are research clues requiring independently checked geometry.
The BKG nationwide KOSTRA model and Berlin sewer-coupled SRGK differ
in hydrology, vintage and coverage and must not be conflated.

## CI and scientific gating

The dedicated .github/workflows/berlin-srgk-schema-hits.yml
runs eight synthetic no-network tests on pull requests. One
reviewed live original-source run is permitted only on main
or by a separately authorized manual workflow dispatch. It
fails closed on unknown provider response semantics.

Offline command:

    python -m unittest tests.test_berlin_srgk_wfs_schema_hits_v0 -v

**The live source result for this new three-operation experiment is
pending its dedicated main run.** No flood depth, model availability,
risk, CAT loss, annual event rate or insured TIV is admitted.

Next: if original schema reveals a geometry property, independently
review supported WFS Filter Encoding spatial predicates and choose
a safe, bounded source probe; preserve the original bbox intersection
gate throughout.
