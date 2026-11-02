<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT 2026 / Overture 2026 building identity pilot

**Research-only. No confirmed real cross-provider individual building matches yet.**

## Two official original source families

Luxembourg ACT GeoBase Buildings (release **2026-10-01**, declared EPSG:2169): original ZIP SHA-256
6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3;
extracted GPKG SHA-256 ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676.
The previously verified ACT original has **230,353 source polygon features**. Source and licence:
https://data.public.lu/en/datasets/bd-l-geobase/ and
https://github.com/pokekarten/OpenCatastrophe-data/pull/1087 .

Overture Buildings (release **2026-10-21.0**, WGS84 lon/lat) are stored as GeoParquet under
s3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type=building/ .
The first two globally listed objects have verified metadata-only receipts in PR #1107;
**neither is known to cover Luxembourg**. Full file SHA-256 and individual original source rows
are not yet verified. Overture licensing/attribution: https://docs.overturemaps.org/attribution/ .

## What the new joined-screen code does

The offline script research_runners/luxembourg_act_overture_identity_preflight_v0.py
accepts a strict JSON projection of **up to 64 ACT and 64 Overture features**, with a maximum
**256 KiB** local input, exact pinned original release and ACT hash *claims*, one original
Overture part key, source families, and Polygon/MultiPolygon coordinates. No source fetching,
no Git/raw geometry upload, no Neon write and no insurer valuation is performed.

An ACT feature carries source_id plus its native EPSG:2169 geometry.
An Overture feature carries gers_id, source_families and EPSG:4326 geometry.
The script transforms Overture lon/lat to the ACT EPSG:2169 national grid using
pyproj always_xy and screens source topology, coordinate envelope, physical area, duplicate
IDs and exact source key/version. It computes planar intersection-over-union in projected
square metres and accepts only reciprocal one-to-one **geometric candidates** with IoU >= 0.75.
A 0.01 m² minimum positive overlap suppresses numerical slivers from coordinate round trips;
one-to-many and many-to-one cases are quarantined, and a no-match applies **only** to the
supplied source slice. The public output is aggregate-only: no building identifiers or
coordinates, only counts, sample SHA, and explicit false admission/provenance flags.

**Scientific caveats:** ACT 2026-10-01 predates the LUREF2025 2026-10-31 reference-frame
change. Transformation does not certify source epoch/physical location accuracy.
A UUID does not confirm GERS registry membership. Overture may use upstream geometry lineage
also present in ACT/OSM, so overlap does not establish independent ground truth.
This is NOT a rights approval, insured property, TIV, CAT vulnerability input or certified
national building stock.

## Specific next original-data acquisition step

Use the official Overture DuckDB spatial bbox method to query a small reviewed Luxembourg
research area and retain the actual returned per-feature **filename**. The source query
uses the frozen 2026-10-21.0 buildings partition and these bounding predicates:

    WHERE bbox.xmin < 6.131 AND bbox.xmax > 6.129
      AND bbox.ymin < 49.611 AND bbox.ymax > 49.609
    LIMIT 25

This is **only a suggested query, not an executed acquisition**. LIMIT bounds returned rows,
not Parquet bytes read. The source may span many objects; separate per-file provenance is
mandatory rather than attaching arbitrary output to the first globally listed file.
See https://docs.overturemaps.org/getting-data/duckdb/ .

On the ACT side, verify the original ZIP/GPKG with the existing full-source
checksum/geometry gate in PR #1087, retain original IDs/coordinates only in ephemeral
private input, and quarantine the previously identified 66 self-intersecting source polygons.
Build a small same-area source-pair JSON projection, then run:

    python -m research_runners.luxembourg_act_overture_identity_preflight_v0 --input /tmp/lu-act-overture-research-only.json
    python -m unittest tests.test_luxembourg_act_overture_identity_preflight_v0 -v

No real ACT/Overture source pair has yet passed this join. ACT hash strings in a JSON envelope
are not proof the individual supplied ACT rows came from the hashed original; Overture whole
file hash/rights still need independent verification. **No permission to load geometry
into the insurance production Neon database or mix with the Pokémon database.**
