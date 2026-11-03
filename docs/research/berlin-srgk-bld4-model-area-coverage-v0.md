<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed SRGK: fixed BLD4 pilot model-area coverage

**Research only; source coverage is NOT verified until the reviewed
original-source workflow succeeds.** This is a separate scientific
question from the BKG signed Int16 water-depth unit and NoData blockers.

## Authority and need

The [official Berlin SRGK catalogue](https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef)
publishes the detailed 1D sewer/2D overland pluvial-storm modelling
product, with attribution requirements under CC BY 4.0.
Its [official WFS technical description](https://gdi.berlin.de/data/ua_srgk/docs/Datenformatbeschreibung_02_24_2srgk2023.pdf)
names a **model-area polygon layer** with fields `gisid`, `layer`
and `jahr`. Water-level rasters are instead supplied through an
Atom feed; a WFS model-area polygon cannot prove depth raster value
availability, scenario calibration, BKG compatibility or any insured loss.

The [Berlin 2026 mapping explanation](https://www.berlin.de/umweltatlas/wasser/starkregen/fortlaufend-aktualisiert/kartenbeschreibung/)
confirms coverage is **selective**: locally reviewed 1D/2D studies are
being added over time; they do not encompass every central-Berlin
building by default. This requires a location-specific geometry proof
rather than inference from the general Berlin city data catalogue.

## Controlled source access / review

`research_runners/berlin_srgk_model_area_pilot_coverage_v0.py`
uses at most **two** exact, provider-locked, public read-only WFS 2.0
`GetFeature` requests against
`https://gdi.berlin.de/services/wfs/ua_srgk`:

1. Fixed **single-feature source existence** control for the exact
   official `ua_srgk:a_modellgebiete` layer. This rules out treating a
   totally empty model-area service as positive coverage.
2. Fixed `EPSG:25833`, `BBOX=391700,5819950,391900,5820150`
   (the original 200 × 200 m BLD4 study polygon) with
   `count=1`. This is a narrowly bounded **pilot intersection
   sample**, not full model-area inventory or real building attribution.

Both requests enforce HTTPS, exact response URL/no redirects/proxies,
40-second timeout, max 786,432 bytes per response, GeoJSON content type,
a strict feature-count cap, duplicate-key/invalid-number rejection and
original CRS EPSG:25833. For a positive BBOX result, a source polygon
must also have a genuine positive-area intersection with the exact BBOX,
verified using the pinned Shapely spatial runtime. Original feature IDs,
addresses, raw polygon coordinates, provider JSON and buildings are
never written to Git/Neon or emitted into logs; only response lengths,
full-body SHA-256s, UTC, aggregate coverage decision and source
non-admission flags are printed.

**Fail-closed scientific interpretation:**
- A positive polygon intersection would establish the BLD4 box touches
  a **detailed model area** at the source snapshot—not that actual
  detailed water-depth raster pixels, entrances or insurer risks are
  available or licensed for CAT use.
- An empty BBOX response, even with positive global source control,
  yields `PILOT_COVERAGE_UNRESOLVED_EMPTY_SOURCE_RESPONSE`, *not*
  `no flood risk` or a proof that no polygon exists.
- Any missing/wrong CRS, incoherent counts, unsupported GeoJSON or
  source geometry outside the frozen BBOX causes a blocker. Any
  provider API variation requires a separately reviewed amendment,
  not silent parser tolerance.

The reviewed GitHub workflow
`.github/workflows/berlin-srgk-model-area-pilot.yml` runs
adversarial synthetic-only checks on PRs. It performs the two bounded
original WFS operations **only after the workflow file change merges
into main** (or explicit reviewed manual dispatch).

## Outstanding

1. Run original provider test and record exact source receipts and
   intersection decision; review time-sensitive service updates.
2. If the pilot intersects a model area, independently verify
   matching detailed SRGK Atom raster product, storm scenario,
   specific source/term restrictions, CRS/units, vintage and actual
   raster cell support before any BLD4 overlay.
3. Do not convert the separate BKG KOSTRA raw Int16 codes to centimetres
   or metres until [the original BKG encoding issue](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086)
   is resolved with provider-linked evidence. Models have different
   hydrology, resolution, vintages and coverage.

No original flood depth or geometry data are saved. No CAT model,
insurer portfolio, TIV, vulnerability or loss is approved here.


## First original WFS evidence: spatial filter failed closed

The reviewed original main workflow
[41354987880](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354987880),
on merged commit `0836a963651d8f251ff675e9d4221244a0bf03db`,
completed all **seven synthetic tests**, but its live official
`GetFeature` pilot request **failed**:

```text
BLOCKED: returned BBOX feature has no positive pilot intersection
```

This means a polygon was returned for the exact
`EPSG:25833` BBOX, but its actual validated EPSG:25833 geometry
did **not** overlap the fixed 200 × 200 m study box. This is neither
a positive detailed-model-area coverage proof nor a verified absence
of detailed models in the area. The WFS could ignore the BBOX, use
different spatial filtering conventions, or exhibit a service bug;
the original run does **not** establish the mechanism.

The current follow-up appends **no broader source query**. It records
only the SHA-256 and byte counts of the two existing fixed original
WFS responses, plus whether they are exactly byte-identical, whenever
the spatial filter is untrusted. The strict **nonzero/fail-closed**
scientific result is unchanged. Original feature names, geometries,
addresses, IDs and raw response bytes are never exported.

Next: review the new original provenance-only diagnostic receipt.
If both bodies are byte-identical, that is evidence consistent with
the provider ignoring or not enforcing this BBOX, not authority to
guess there is no detailed model covering the pilot. A further
provider-specific `DescribeFeatureType` and FES spatial-filter
review may be necessary before a new **bounded** geometry query.


## Original XSD geometry-property identity and FES experiment

The reviewed [official source DescribeFeatureType run
41355903211](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355903211)
on merged commit `94f1e20aa4fbb187e7e5765327cfba2be3014f4a`
returned original **1,389 XSD bytes**, SHA-256
`8112bf8db14b7f3f1cb516717e128e0a450b643e645c29b1955e6c69bd57b87f`.
Its unique, source-declared model polygon geometry field is:
`geom`, type `gml:MultiSurfacePropertyType`.
Seven synthetic schema tests and the original XSD check succeeded.
No source model-area polygon, address, TIFF or original XSD body was stored.

A new **separate** fixed-source FES 2.0 `Intersects` canary
`research_runners/berlin_srgk_fes_model_area_pilot_v0.py`
refers to this exact evidence, but **must not** claim official pilot
coverage until its own source run succeeds. The operator explicitly
filters `geom` against the frozen EPSG:25833 200×200 m envelope,
rather than relying on the previous inconsistent WFS BBOX parameter.
Both the one-feature control and exact FES-filtered response are
independently parsed, checked for source CRS and truly intersecting
polygons; only SHA-256s, sizes, aggregate overlap and negative
model-admission flags may be logged.

A positive overlapping polygon means at most one detailed-model
**study area** touches the pilot, **not** water-depth raster availability,
building hazard, event probability or insured loss.
If the provider returns a non-overlapping polygon, the FES result
is explicitly **BLOCKED**, and if it returns no model polygon, coverage
remains **UNRESOLVED** rather than a claim that the buildings are dry.
