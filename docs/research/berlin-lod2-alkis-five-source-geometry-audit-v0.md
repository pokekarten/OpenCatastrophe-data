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

## First real original source outcome

Pending successful source-specific live GitHub Actions execution.
Do not claim measured roof heights, complete Berlin source coverage
or positive 1:1 geometry matches from synthetic tests alone.
