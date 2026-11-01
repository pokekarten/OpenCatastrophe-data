<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# One exact source window: Berlin ALKIS vs 2022 height count-only audit

A prior original-source comparison successfully retrieved five ALKIS and
five Umweltatlas LoD2 2022 building-height feature polygons but found
**zero** one-to-one IoU≥0.95 spatial matches. This is **not** evidence
of no spatial correspondence: each WFS `count=5` returns an
independent, provider-order-limited first five records; full
source coverage and pagination were never verified.

Verified original source proof:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323489470

## Next scientific verification without provider geometry downloads

`research_runners/berlin_alkis_lod2_bbox_hits_v0.py`
executes **exactly two** original official WFS2.0 GetFeature
`resultType=hits` operations, one for each independently verified
building source, in the **same fixed Berlin EPSG:25833 200m×200m box**
`391700,5819950,391900,5820150`.

1. `alkis_gebaeude:gebaeude` current mutable official Berlin ALKIS;
2. `ua_gebaeudehoehen:gebaeudehoehen` official Berlin Umweltatlas
   LoD2 **2022/2023 updated** derived product.

These requests are count-only, `count=1`, limited to
128KiB and 35s each, with fixed HTTPS/host/feature name/bbox, no
user filters, redirects or external proxy. The parser permits only
OGC WFS 2.0 `FeatureCollection` with explicit bounded integer
`numberMatched`, `numberReturned=0`, no unexpected member objects,
no XML DTD/entities. Any `unknown`, error document, HTML, unexpected
feature data or huge count must fail closed.

Outputs are the two exact **in-box candidate counts**, original XML
response byte lengths/SHA-256, UTC and script hash. Counts do **not**
prove building completeness, segmentation, number of *physical*
buildings, historical equivalence or number of matched source
features. Separate count-only evidence is a prerequisite for
defining a bounded **full-in-box** two-provider polygon analysis
instead of comparing arbitrary first five records.

The two catalogues list **Datenlizenz Deutschland – Zero 2.0**:
- https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a
- https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d

The workflow `.github/workflows/berlin-alkis-lod2-fixed-bbox-hits.yml`
runs synthetic only on PR; one exact first-party live check on its
reviewed workflow file merge to main or maintainer manual dispatch.

No geometry, private address, height, original source ID, insured
value or original properties are requested or stored. No persistent
CAT/Neon/Pokémon DB is touched and no model data admitted.

## Source-count real receipt

Pending verified original-source WFS2.0 run. Do not substitute the
`count=5` source limit for `numberMatched` or claim that the
two products have the same exact geographic content.
