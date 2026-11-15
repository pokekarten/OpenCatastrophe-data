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

The hits parser now requires an **explicit**
`numberReturned="0"` and an entirely empty source
`FeatureCollection` (no child objects, unknown feature elements or
non-whitespace text). The service's count is rejected rather than
silently accepting any unreviewed source-feature payload.

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

## Verified original official WFS count-only evidence — 2026-11-01

Source-side first-party
[GitHub Actions run 41323901716](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323901716),
merged main commit `4d32687473d1bcab49cab998ab86cb2f48e056a8`,
source UTC `2026-11-01T15:58:41.623712+00:00`:

| Source WFS2.0, same fixed EPSG:25833 200m bbox | Official numberMatched | numberReturned | XML bytes | Original SHA-256 |
| --- | ---: | ---: | ---: | --- |
| Current ALKIS `alkis_gebaeude:gebaeude` | **18** | 0 | 837 | `509c38e02796fb1e69e8ba53c5eb3eafd6412b4a7f410ad7d1921cb4a146461f` |
| Umweltatlas LoD2 2022 `ua_gebaeudehoehen:gebaeudehoehen` | **27** | 0 | 849 | `29530fdf528f78555c18a91be385998fe4260faae320ef134e21e3003c318405` |

This is definitive first-party proof that both **first-five** source
responses from the preceding IoU study were incomplete: the official
services report **18 and 27** candidate source *features* in the same
window. This does not establish the number of physical buildings,
whether parts/roof facets appear, or whether individual 2022 features
still exist in 2026.

A narrowly scoped next original-data challenge may now fetch at most
50 features per source in the same frozen bbox, require that each
returned FeatureCollection reports complete `numberMatched` and
`numberReturned` exactly equal to its returned feature count,
and run actual one-to-one projected IoU matching against both
source populations. Both source releases remain mutable; their count
may drift after this timestamp and should never be rewritten silently
to force a successful check.
