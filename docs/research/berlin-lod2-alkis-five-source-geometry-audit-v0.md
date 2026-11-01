<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Real Berlin LoD2 2022 height vs monthly ALKIS building source audit v0

**Separate product and vintage proof**, not a building-enrichment join in
an insurer production database.

Official Berlin 2022/2023 Umweltatlas building-height dataset:
https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d
source service `https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen`,
layer independently confirmed in first-party
[GitHub Actions run 41322717682](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41322717682)
as `ua_gebaeudehoehen:gebaeudehoehen`, WFS 2.0.0,
EPSG:25833 supported; original public metadata SHA-256
`29911c913544dd1e04ef75fb370ff6d5729de9fa50d26f62634830b1effcd642`.

Official Berlin monthly ALKIS building source:
https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a,
layer `alkis_gebaeude:gebaeude`, WFS 2.0.0, EPSG:25833.

Both publisher catalogues label **dl-de-zero-2.0**. Source rights
still require model-specific admission, and original layer geometry
vintages differ: the height product stems from **2022 LoD2 / 2023
update**, while current ALKIS is monthly updated. The height source
officially states its footprint and ALKIS geometry origins are related;
the height product therefore cannot be counted as wholly independent
ground truth.

## Bounded actual source audit

`research_runners/berlin_lod2_alkis_five_polygon_comparison_v0.py`
performs exactly **two** anonymous official WFS 2.0.0 GetFeature
requests in one securely bounded evaluation. Both fixed to a **single
EPSG:25833 200m×200m** Berlin research box
`391700,5819950,391900,5820150`, each with `count=5`,
`outputFormat=application/json`, max 512KiB/35s, no redirects,
proxy, arbitrary IDs, filter, bbox, host or full-country pagination.

- Each original polygon must be an OGC-valid, positive-area
  Polygon/MultiPolygon intersecting the selected query box by
  **positive area**, with plausible Berlin projected axes. Repeated
  source feature IDs/geometries and malformed/unknown CRS fail.
  **Both original GeoJSON replies must explicitly declare EPSG:25833**:
  the WFS `srsName` request alone does not prove the reply's native
  coordinate semantics, and silent conversion from CRS-less GeoJSON
  into metre-space could fabricate source geometry matches.
- Compare up to 5 ALKIS and 5 independent-height polygons **in
  EPSG:25833 metric geometry**. Count pairings only where projected
  original footprint intersection-over-union **IoU >=0.95**.
  A valid match must be **one-to-one on both sides**. An unmatched
  result is not evidence a building has no height; each provider
  independently caps its returned five *unordered* features.
  A candidate that maps to several source objects is ambiguous,
  **not** flattened into one insured risk.
- Only public **aggregate** heights, role and property-completeness
  statistics are output: `hoehe` positive-number count, exact
  3m possible placeholder count, `role_txt` explicit building vs
  building-part counts, `dachart`, `geschosse` and source
  `quelle*` method-field non-null counts. **No original values,
  building IDs, addresses, names or feature coordinates** are logged.
- A 3m value may be an imputed/default building height under original
  published methodology. **No value can be asserted measured**
  solely from `hoehe`. This proof does not transfer any height
  into a 2026 ALKIS building record or CAT4 modelling asset.
- Source response byte counts/individual SHA-256 + UTC + script SHA
  recorded; raw feature bytes and attributes held in memory only.
  Absolutely **no persistent CAT/Neon/Pokémon DB modification**.

Synthetic only on pull requests. The dedicated exact-source workflow
performs the **one one-shot live two-provider test** after reviewed
merge of its own workflow revision on main, or explicit manual dispatch.

## Scientific next gates

For a valid building-level height enrichment, ensure *all*
candidate polygons in a bounded scope are independently paginated
and deduplicated (not merely first five); identify true building
versus Bauteil relations, calculate source coverage and temporal
drift against original cadastral footprints, tie `rolle`,
`hoehe`, estimation methods and construction-vintage uncertainty
to **unique validated source relationships**, and keep all source
versions in a separate CAT database. Do not infer replacement value
from polygon area or roof height alone.

## First real original source outcome — 2026-11-01: bounded negative match

The reviewed original-source [GitHub Actions run 41323489470](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323489470)
completed successfully on main commit
`77ca0b24e85e0c606433dff5baa6258221884b7c`, UTC
`2026-11-01T15:53:42.930923+00:00`. Six synthetic regression
tests passed first. The official source returned:

- Current ALKIS: **5** accepted source polygons, **5,412** response bytes,
  SHA-256
  `70bcc04acd6498dec52538f2d6edbc189dcab5e7004fafb0318069b8d6f7bce5`.
  The combined source footprint area is **1,344.0 m²**, which is NOT
  the inventory or total area within the bbox.
- Historical height WFS: **5** accepted source polygons,
  **7,874** response bytes, SHA-256
  `385a42facd9713bdb185465e49a4cb929d98bd87b24c950caf96a9a89abbf859`.
  All five sampled polygons had non-null source attributes for
  `hoehe`, `dachart`, `geschosse`, `role_txt`,
  `grundrissaktualitaet`, `quellebodenhoehe`,
  `quelledachhoehe` and `quellelage`.
- **5 of 5** recorded positive numeric height values; **0** exact
  3 m values in this tiny sample. This is NOT evidence that all five
  values were measured or that the height product never imputes values.
- Aggregated `role_txt`: **2** explicitly classified as buildings,
  **0** explicitly classified as parts, **3** unknown under the
  conservative source-value classification. Do not recode unknown as
  building or count 5 separate physical buildings from this product.
- **0** unique pairs passed the research threshold **IoU ≥ 0.95**;
  **0** ambiguous candidate incidences passed the same threshold.

**Interpretation:** This is a validated **negative source-pair result
for the two fixed first-five source samples**, not proof the products
have no common physical buildings. WFS `count=5` is not a reproducible,
complete inventory for the 200 × 200 m query box. It does not establish
coverage, imputation prevalence, source independency, temporal drift,
building ownership, insured values, or any model-input admission.
Original responses, coordinates, feature IDs and actual height values
were not saved.

A subsequent fail-closed regression in
[PR #1003](https://github.com/pokekarten/OpenCatastrophe-data/pull/1003)
requires **explicit EPSG:25833 declarations in both provider replies**
before such a two-source IoU comparison. That protection was added
*after* the original source run and is not retroactive evidence of
the exact 2026-11-01 response CRS flags. A future provider sample
must independently pass this stricter gate.

Next research must first review exact official WFS paging and stable
ordering/whole-bbox coverage, use a source-approved bounded query or
independent spatial selection, distinguish LoD2 building vs part and
historical release dates, and quantify one-to-many polygon relations.
Never force a match by using source names, original IDs, addresses or
unreviewed coordinate assumptions.

## Verified two original sources — zero *first-five* matches, 2026-11-01

First-party GitHub Actions
[run 41323489470](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323489470),
main commit `77ca0b24e85e0c606433dff5baa6258221884b7c`,
verified both *official fixed* independent source requests,
geometry and source attributes at
`2026-11-01T15:53:42.930923+00:00`.

| Evidence | Real observed source |
| --- | --- |
| 2026 ALKIS five polygons | 5, source response 5,412 bytes |
| ALKIS response SHA-256 | `70bcc04acd6498dec52538f2d6edbc189dcab5e7004fafb0318069b8d6f7bce5` |
| 2022 LoD2 height source five polygons | 5, source response 7,874 bytes |
| LoD2 response SHA-256 | `385a42facd9713bdb185465e49a4cb929d98bd87b24c950caf96a9a89abbf859` |
| Height values `hoehe` positive numeric | 5 |
| Source `role_txt` = recognised Gebäude | 2 |
| Recognised Bauteil | 0 |
| Unrecognised/missing role labels | 3 |
| `dachart`, `geschosse`, `grundrissaktualitaet`, `quellebodenhoehe`, `quelledachhoehe`, `quellelage` populated | 5 each |
| Exact height = 3m possible placeholder | 0 in this five-feature sample |
| Unambiguous ALKIS ↔ LoD2 polygons at IoU≥0.95 | **0** |
| Ambiguous individual candidates at IoU≥0.95 | 0 |
| Original feature bytes or properties committed/persisted | No |

**Critical:** This does not demonstrate non-coverage or physical misalignment
of the underlying 2022/2026 Berlin building layers. Both query
parameters apply **count=5 independently**; different first-five
ordering/populations can lead to zero shared records even with perfect
alignment on complete geographic data. The correct next proof is to query
**counts-only GetFeature `resultType=hits`** for the same tiny fixed box,
then, if count fits a reviewed response budget, acquire the complete
in-box source populations with bounded pagination and explicit duplicate
and one-to-one topology controls. Never solve this by weakening the
IoU threshold, name/address joins, or imputing roof height into CAT4.
The three unknown role labels also require checking actual source
classification semantics, not inventing a building/part count.
