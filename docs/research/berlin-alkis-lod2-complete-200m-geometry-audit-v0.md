<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Full-in-query-box official Berlin ALKIS vs LoD2 2022 geometry and height audit

## Why this is the correct next source step

Prior independent live official WFS2.0 count-only source proof
[run 41323901716](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323901716)
confirmed **18 ALKIS building features** and **27 Umweltatlas LoD2
2022 height features** in the same frozen 200m × 200m research box in
EPSG:25833 (UTC 2026-11-01T15:58:41+00:00). The earlier 5×5 first
features had zero one-to-one IoU≥0.95 matches, an
**incomplete-ordering artifact** that must not be used to conclude
that the height product lacks spatial correspondence.

## Strict source-specific complete extraction

`research_runners/berlin_alkis_lod2_complete_bbox_v0.py` performs
**one** official anonymous WFS GetFeature request per independently
reviewed source at fixed 200m bbox
`391700,5819950,391900,5820150,EPSG:25833`,
`count=50`, `outputFormat=application/json`, WFS2.0:

- `alkis_gebaeude:gebaeude` from official monthly ALKIS Berlin,
  <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>.
- `ua_gebaeudehoehen:gebaeudehoehen` from independent-source product
  Berlin Umweltatlas **2022 LoD2 height**, updated 2023,
  <https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d>.

Each HTTPS response is bounded by **768 KiB, 45 seconds, no redirects
or proxies**, and the code rejects unknown hosts, CRS, untrusted
queries, changed feature types, empty/malformed GeoJSON,
invalid/duplicate original feature identity, nonpolygon geometry,
nonfinite/invalid coordinates, unreasonable areas and out-of-scope
polygons. Most importantly, it **requires source-provided integer
`numberMatched` and `numberReturned` to be equal to the actual
number of features returned**, with at most 50 features per source.
If the 2022/2026 live source data now have more than 50 features
in the same fixed study box, the research stops rather than claiming
a complete sample.

Once complete source sets exist in memory, the audit computes all
original spatial polygon intersections/union areas in the same
projected coordinate space. Only one-to-one original footprint pairs
with **intersection-over-union (IoU) ≥0.95**, with no conflicting
other matching candidate, count as unambiguous spatial matches.
This does *not* claim a permanent source identifier equivalence, 2022
to 2026 physical stability, actual replacement value, or insured
portfolio inclusion.

The source-only safe receipt includes all current in-box feature
counts, unmatched original feature counts, unique unambiguous polygon
pairs, candidate ambiguity, and **aggregate counts** for
`role_txt` (building vs Bauteil), `hoehe`, `dachart`,
`geschosse`, `quelle*` estimation methods and possible **3m
placeholder** roof heights. No raw source identifiers, geometry
coordinates, individual heights, addresses, attributes or provider
feature values are logged, saved, committed or transferred into
CAT/Neon/Pokémon databases. In particular no heights are admitted to
an insurer model by this research code.

The dedicated `.github/workflows/berlin-alkis-lod2-complete-bbox.yml`
runs source-free synthetic tests on PR; a reviewed workflow-file
change triggers **one** bounded real two-source experiment on main.
No nationwide recurring crawler or bulk downloader is enabled.

The results must distinguish official *feature* counts from unique
physical buildings. The 2022 LoD2 height product contains building
and building-part polygons and some 3m imputed first-height values;
an insurer property may overlap one or several source polygons.
Product vintages and original data rights (both official catalogues
list **dl-de-zero-2.0**) remain explicit. The height product reuses
ALKIS-related footprints upstream and is not an independent precision
ground-truth provider.

## Original-source result

Pending the first reviewed original WFS execution.
Only successful source-run evidence can establish the actual
complete-in-bbox polygon IoU and height/role counts. Synthetic tests
are *not* evidence of measured/verified real building heights.
