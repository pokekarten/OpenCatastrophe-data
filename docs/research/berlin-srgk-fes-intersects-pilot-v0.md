<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original Berlin SRGK model area – FES 2.0 Intersects check (v0)

**Research-only, source-readonly. Original FES run completed, but the
model-area coverage remains unresolved.** The reviewed main
[Actions run 41356416551](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41356416551)
on commit 6dfecf2b12da1891e02dbde2ec01515aff6d788b
successfully checked the original schema SHA and queried one fixed
source FES Intersects filter on geom, but returned **zero features**.
The original response was **147 bytes**, SHA-256
e2c6d7478391162bb8f89e2fb0c877013bac02fd12ff83b6084e14019d2b71a4.
This does **not** prove lack of model coverage or no flood risk:
the independently recorded WFS BBOX hits probe returned one
pilot hit and earlier GetFeature BBOX returned a nonintersecting polygon.

The separate [source-linked TOML research receipt](berlin-srgk-original-wfs-hits-fes-disagreement-20261101.toml)
locks both original independent runs and explicit no-coverage/no-risk
nonadmission. They were not an atomic source snapshot. A future
provider filter implementation must reconcile these results without
silently changing the fixed BLD4 test bbox or bypassing the
positive-area intersection gate. No building risk, flood depths
or insurance CAT input are admitted.

## Why this is an independent check

The original Berlin detailed Starkregengefahrenkarte
ua_srgk:a_modellgebiete WFS on
https://gdi.berlin.de/services/wfs/ua_srgk returned a polygon that
did not intersect the exact 200-by-200-metre BLD4 study box when
requested through BBOX on the initial
[run 41354987880](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354987880).
That observation is preserved by [PR #1093](https://github.com/pokekarten/OpenCatastrophe-data/pull/1093);
its original polygon-intersection gate must remain strict.

A separate [original schema/hits run 41355919644](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355919644)
reported **8 source model-area features globally and 1 hit**
under the same BLD4 BBOX, while original
DescribeFeatureType identified public geometry property **geom**
(original XSD SHA-256
8112bf8db14b7f3f1cb516717e128e0a450b643e645c29b1955e6c69bd57b87f,
1389 original XML bytes). A *hits* count does not prove
geometry intersects the BLD4 pilot.

[PR #1095](https://github.com/pokekarten/OpenCatastrophe-data/pull/1095)
is a separately reviewed original geometry-field proof and is
not changed by this work.

## New source-specific FES experiment

The new script
research_runners/berlin_srgk_fes_intersects_pilot_v0.py
makes exactly two original provider operations, bounded to the
same official host:

1. Original WFS 2.0 DescribeFeatureType, at most 512 KiB; require
   the pinned independent original SHA-256 and a unique public
   geometry property candidate named geom. No unknown schema accepted.
2. Original WFS 2.0 GetFeature count=1 with an explicit
   **Filter Encoding Specification 2.0 Intersects** expression
   against property geom and the **frozen** BLD4 study envelope
   (391700,5819950,391900,5820150), EPSG:25833. GeoJSON
   response max 786,432 bytes. No source URL, area or filter
   can be supplied by a caller.

The original returned geometry is parsed entirely in temporary
memory with the original CRS check and polygon validity gate.
A **positive, finite, at-most-40,000m² exact polygon intersection**
with the pilot is mandatory before a local sampled
model-area overlap is reported. Absent source features are
**unresolved**, not proven absence of any hazard or model.
An unrelated returned polygon or unrecognized source version
fails closed. No original feature ID, geometry, attribute, WFS
JSON response, building identification or location list is
persisted or printed. Only **aggregate intersection area**,
full response SHA-256, byte length and nonadmission flags
are reported.

A positive intersection would establish *one* pilot-level
detailed **model-area polygon** at one source snapshot.
It would NOT prove actual local storm-scenario water-depth
raster cells, rain event probability, damage, source licences,
property entrance elevations, vulnerability, insured TIV,
loss, or scientific equivalence to the separate nationwide
BKG KOSTRA Int16 dataset. Even a known geometry property
does not establish universal WFS filter support.

## Tests and original-source gate

On pull requests only synthetic tests run, including
positive/negative source features, invalid CRS, nonintersection,
count-only negative scenarios, source schema SHA drift,
explicit filter identity, oversized/unexpected content,
and source-geometry/ID non-exfiltration.

Reproduce locally:

    python -m unittest tests.test_berlin_srgk_fes_intersects_pilot_v0 -v

The dedicated GitHub workflow installs pinned spatial dependencies,
runs offline adversarial tests on PR, then checks the actual
source **only after reviewed merge to main** or an explicit
manual workflow dispatch. If the official WFS responds with
an exception or ignores the FES filter, the runner
**must block rather than lower the spatial acceptance threshold**.
