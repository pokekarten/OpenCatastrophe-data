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
