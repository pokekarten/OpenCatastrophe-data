<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed SRGK: independent second model-area pilot candidate

**Research-only. Original source observation pending after review.** This
is a geographically separate, provenance-pinned candidate for *future*
detailed Berlin 1D sewer/2D overland model comparisons, not a physical
depth raster, insurance location or completed CAT model.

## Verified first-pilot source disagreement

The original [fixed BLD4 WFS BBOX counts run
41355919644](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355919644)
reported 8 model-area polygons overall and 1 candidate BBOX hit, but
the GetFeature BBOX returned a **nonintersecting polygon**. The
later source-locked explicit FES `geom` Intersects source request
[41356270347](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41356270347)
returned **zero** actual pilot features. This disagreement is
preserved in the
[source-vintage receipt](berlin-srgk-original-wfs-hits-fes-disagreement-20261101.toml).
It is neither a valid hazard-free finding nor a proven first-pilot model
area. The checked official
[SRGK WFS technical description](https://gdi.berlin.de/data/ua_srgk/docs/Datenformatbeschreibung_02_24_2srgk2023.pdf)
independently identifies a model-area layer; water-level raster sources
are separate Atom products.

## This narrow source-anchored pilot experiment

`research_runners/berlin_srgk_second_model_area_candidate_v0.py`
issues exactly **one** allowlisted anonymous WFS 2.0 `GetFeature`
(`typeNames=ua_srgk:a_modellgebiete`, `count=1`,
`srsName=EPSG:25833`) after the workflow is reviewed and merged.
It accepts at most 786,432 original GeoJSON bytes, no redirects,
proxies or unverified CRS/geometry, rejects duplicate keys,
wrong media types, invalid/nonfinite polygons and data outside a
conservative Berlin EPSG:25833 envelope.

The derived candidate is a **new 200×200-m study box** centered on
an in-polygon representative point of the one sampled official model
polygon, deterministically snapped to a 20-m grid. Its positive polygon
overlap is independently calculated and must be at least 10 m².
It is explicitly rejected if it intersects the prior 200×200-m BLD4
box. One sample is **not** a census of all published model areas,
and the candidate may not be completely inside the source model polygon.

Only the derived public pilot **box**, rounded aggregate overlap area,
full source response SHA-256, byte size and UTC are reported.
Original polygon coordinates, feature IDs, addresses, private
attributes, detailed raster pixels and any insurer data are not
printed, committed or written to Neon.

**Critical next admission gate:** A future separately reviewed
`geom` FES 2.0 `Intersects` query must independently prove that
the provider itself returns the official detailed model-area polygon
for the **new fixed candidate box**. A local intersection on the
unfiltered source polygon is insufficient evidence of correct
provider spatial-filter semantics; the previously observed source
mismatch is an explicit reason to require this independent check.

A successful future area match still would not establish the exact
matching detailed Atom water-depth GeoTIFF, scenario, CRS, physical
scale, source licensing, insured building exposure or loss.

## Tests

Seven deterministic synthetic-only tests cover in-polygon
representative point, distinct old/new boxes, source SHA, wrong CRS,
out-of-Berlin coordinates, duplicate GeoJSON keys, wrong content
types, oversized content and source data non-disclosure. The
workflow fetches no official source bytes on pull requests. A
reviewed push-to-main activates only the one fixed public provider
GetFeature request.

This does **not** change
[the BKG Int16 unit/scaling blocker](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086):
a nationwide 1-m horizontal resolution is not a certified vertical
water-depth conversion. The independent old BLD4 model is retained.
No real CAT model input is admitted.

## Original first-source candidate verified; independent filter pending

The reviewed original [source-derived second pilot run
41363179064](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363179064),
merged from [PR #1102](https://github.com/pokekarten/OpenCatastrophe-data/pull/1102),
succeeded on main commit
`45f637f8d381480c794fefba6c14605ae969a098`.
The exact fixed original WFS `GetFeature count=1` response was
**10,883 bytes**, full SHA-256
`62d6c31ef5dd17227aad35afd740031eff9f7343f50bff99d941a0c822ff95d5`,
observed `2026-11-01T23:39:48.617487+00:00`.

One official polygon yielded a **new distinct** fixed
EPSG:25833 200×200 m study bbox
`[391860,5816840,392060,5817040]`, with **40,000 m²**
independently measured local intersection. Only derived coordinates,
source response hash, aggregate area and scientific nonadmission
flags were logged; no original geometry or feature ID was stored.

This is a **source-derived local geometry witness**, not yet
independent server-side spatial-filter evidence. The next separate
reviewed source test
`research_runners/berlin_srgk_second_model_area_fes_proof_v0.py`
will require (a) the original control polygon *still derives the same*
new study box, and (b) a second fixed FES 2.0 `Intersects` on official
`geom` returns a valid EPSG:25833 polygon genuinely overlapping it.

Both response hashes and aggregate overlap area will be reported.
An empty filtered answer remains **unresolved**, not proven absence
of model coverage or rainwater depth; nonintersecting geometry blocks.
A successful FES overlap is **model-area coverage only**, not
actual depth pixels, physical units, insured buildings or CAT losses.
