<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original CEMS EMSN028 2016 FileGDB — layer and topology research, 2026-11-01

**Status: source bytes pinned; 18 geospatial layers read; original flood mask
topologically invalid; AOI04-specific product/rights and model admission BLOCKED.**

This supplements the original [155,898,548-byte ZIP receipt](cems-emns028-original-archive-receipt-20261101.toml).
No original provider bytes, per-building properties, polygon coordinates or
policy-level information are committed. The source archive is downloaded
into a temporary GitHub Actions workspace and deleted after each run.

## Independently executed original-geodata checks

| Check | Evidence |
| --- | --- |
| Full source SHA-256 | `7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2` |
| FileGDB metadata | [run 41347769305](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41347769305): all **18/18** layers open with Fiona 1.10.1 |
| Original layer attribute/topology sample | [run 41348300755](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348300755): successful with Shapely 2.1.2 |
| Coordinate system | EPSG:32631 (UTM zone 31N), independently read from original features |
| `Buildings` | **647,276** source building polygons across package, not observed insurer-specific buildings or verified 2016 building construction state |
| `Flooded_area` | **1** MultiPolygon feature, **59,755** coordinate pairs; satellite/RADAR/optical `src_date=2016-06-02`, `ext_date=2016-08-03` |
| `Estimated_Max_Flood_Extent` | **1,237** features, separate estimated/extrapolated maximum layer; two sampled polygons were valid, **not a full 1,237-feature validity check** |
| `aoi` | **1** broad valid MultiPolygon; 2,279,749,070.82 m². It includes the Ponthierry gauge control but is **not** proven to be the separate AOI04 boundary |
| Other useful layers | Hydrology_area 7,551; Hydrology_line 876; LandUse 33,364; Transportation_line 58,107; Hydrographical_Station 12 |

**Critical failure**: the unmodified first `Flooded_area` feature reports
`geometry_valid=false`, specifically:

`Ring Self-intersection[485697.5986 5358841.9696]` (EPSG:32631).

This finding concerns the **original downloaded FileGDB geometry**, unlike
a separate prior incident where an independently rounded PPRI polygon
became invalid. The `Flooded_area` polygon is **not** eligible for
unreviewed `ST_Intersects`, area, centroids or exposure attribution.
The script refuses to calculate polygon intersection or area when
`is_valid=false`. It does not change the source geometry or issue
`make_valid` automatically.

The source attribute `src_date=2016-06-02` relates to the source
observation/acquisition; `ext_date=2016-08-03` is a distinct recorded
date and **must not** be interpreted as an additional flood observation.
The report's temporal validity and each AOI's satellite acquisition
require separate source documentation.

The first two of the 1,237 estimated polygons each happen to have
an observed sample geometry area of 34.14 m². This is **only a two-row
sample** and is **not** evidence that all 1,237 polygons have this area,
nor evidence of flood depth or loss.

## No AOI04 conflation

The shared `aoi` source layer has one broad polygon and an
`act_id=EMSN028` attribute. The other critical layers likewise
identify the activation via `act_id` rather than an independently
confirmed `AOI04` key. No narrow AOI04 observed flood geometry
can be claimed from the layer names alone.

The official [AOI04 observed flood-extent map](https://mapping.emergency.copernicus.eu/download/EMSN028/EMSN028_04SAINT-FARGEAU-PONTHIERRY_01OBSFLOODEXTENT_DETAILS_v1_100dpi.pdf)
is a cartographic reference, not original vector-mask proof. Even
a mathematically repaired aggregate observed polygon would still
require a correctly sourced AOI04 geometry and temporal assessment.

## Licensing and provider material

The official [EMSN028 maximum-flood overview PDF](https://mapping.emergency.copernicus.eu/download/EMSN028/EMSN028_00SOUTHPARIS_02MAXFLOODEXTENT_OVERVIEW_v1_100dpi.pdf)
is labelled **RESTRICTED USE** and refers to arrangements for access to
authoritative geospatial reference data. Underlying layers include
third-party remote sensing and French national geodata. It would be
incorrect to infer commercial reuse or redistribution rights for the
whole ZIP merely because the archive is technically accessible from
a public URL. The specific product- and layer-level restrictions require
clarification.

The official flood observation, estimated maximum, and inferred
impact products must retain distinct provenance and interpretation.
No model-use permission has been established.

## Reproduction and required next step

Code:
- [Original full layer enumeration](../../research_runners/cems_emns028_filegdb_layer_inventory_v0.py)
- [Original priority-layer sample](../../research_runners/cems_emns028_priority_layer_semantics_v0.py)
- [Machine-readable evidence](cems-emns028-filegdb-topology-receipt-20261101.toml)

To progress safely, resolve **both** independent gates before any
flood-to-building join: (a) approve an explicit, traceable topology
repair/alternative original AOI04 observed extent with area-change and
spatial-error tests; (b) establish exact source-rights, vintage,
independent 2016 building data, AOI04 extent and temporal match.
Then determine a **research-only** overlay on a controlled branch,
without asserting actual insured TIV, claims, vulnerability, or
reinsurance. The open [2016 Seine-et-Marne BD TOPO source research
PR #937](https://github.com/pokekarten/OpenCatastrophe-data/pull/937)
is a potential vintage-aligned building input only after independent
rights/source-byte review.

**No Neon schema, source records or model admission flags changed.**
