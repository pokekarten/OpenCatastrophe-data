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
polygons. **Both original GeoJSON sources must explicitly declare
EPSG:25833**; the WFS request parameter alone is not proof of response
coordinate semantics. Source geometries are also required to be
topologically distinct even when their feature IDs differ, preventing
duplicate-footprint inflation of the matching statistics.
Most importantly, it **requires source-provided integer
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

For *only the uniquely matched polygon pairs*, the new non-admission
quality gate additionally reports aggregate known/unknown building/part
roles, positive numeric heights, exact 3m **possible placeholders**,
non-3m heights **not proven measured**, and the presence of source-method
codes. Even a recognized building role with non-3m height is only a
research-triage candidate: its identity, height method, source 2022/2026
vintage, scientific uncertainty and rights remain independently gated.
No individual height or provider source ID is printed.

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

## First-party full original-source reconciliation — 2026-11-01

The complete source-reported feature populations in the *same fixed
200m × 200m original source EPSG:25833 box* were independently
downloaded, checked and compared in
[GitHub Actions run 41324614040](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41324614040),
merged main commit `6dcab89bec98a7c8f0e8b43c3c212e0b4bf58d10`,
UTC `2026-11-01T16:07:01.947191+00:00`:

| Original-source evidence | Observed value |
| --- | --- |
| Current ALKIS original GeoJSON response | 20,880 bytes, SHA-256 `9f35b57dfcd3336f0cca5735850abb1fe88072de82d16c1163b1579cbce2d945` |
| Official Umweltatlas LoD2 2022 height GeoJSON response | 35,917 bytes, SHA-256 `63a0eeece2b10113016ea56d2e9474a671935bd2201e2dabcc535b3ebf11680f` |
| Independent original `numberMatched=numberReturned=features` | **18** ALKIS / **27** 2022 height features |
| Polygon validity / source CRS / count completeness | All implemented source gates passed |
| Unique one-to-one polygon matches (projected IoU≥0.95) | **6** |
| Ambiguous source candidate incidences at IoU≥0.95 | **3** |
| Not uniquely mapped original feature counts (includes ambiguous ones) | **12** ALKIS / **21** heights |
| `hoehe` positive numeric | **27 / 27** |
| `dachart`, `geschosse`, `grundrissaktualitaet`, `quellebodenhoehe`, `quelledachhoehe`, `quellelage`, `role_txt` non-null | **27 / 27** each |
| Recognized `role_txt` = Gebäude | **2** |
| Recognized literal Bauteil | **0** |
| Other/unrecognized role labels | **25** |
| Exact 3m height possible placeholder | **0** in this sample |
| New heights assigned to CAT4 or insured assets | **0** |
| Original geometry, IDs, addresses or attribute values persisted or logged | **No** |

The first-five 0-match result was a **sampling/order limitation**:
now **6** strictly unambiguous geometric pairings are observed when
testing the actual full 18 and 27 original feature populations.
This proves the overlap method can identify near-identical source
footprints, **not** that six physical insured buildings have independently
measured roof heights.

Do not reinterpret the **25 unknown role labels** as Bauteil or
Gebäude without checking the provider's actual source domain codes.
Ambiguous pairings may represent building-part segmentation and
data-vintage differences. Do not weaken IoU or silently match via
names, addresses or IDs. At most six **candidate** height assignments
exist for future controlled research; **none** have been admitted to
CAT4 or insurer portfolios. The next investigation should inspect
the official role/height-source domain semantics in aggregate, and
quantify coverage/splits before integrating any height attributes.
