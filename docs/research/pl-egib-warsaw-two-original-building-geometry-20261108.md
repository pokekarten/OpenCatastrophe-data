<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Poland EGiB: two original building polygons and WFS 2.0 EPSG:2180 axis guard (2026-11-08)

**Research status:** directly requested original-provider publicly downloadable building geometry (bounded area, two features max), NOT building-source admission. This continues the merged [metadata-only GUGiK WFS contract](pl-egib-buildings-wfs-native-contract-20261108.md). The original source geometry and feature IDs are not in Git.

## Provider rights and scientific caveats

- The GUGiK [official EGiB source and licence explanation](https://www.geoportal.gov.pl/en/data/land-and-building-register-egib/) says building/parcel geometry and **basic attributes** are free for any purpose. This is not blanket clearance for every cadastral field, broader rights, bulk copies or insurer-use constraints.
- The [16 July 2026 GUGiK integrated WFS announcement](https://www.gov.pl/web/gugik/zbiorcza-usluga-wfs-dla-ewidencji-gruntow-i-budynkow-udostepniona-w-modulach-mapowych-serwisu-geoportalgovpl) documents county-origin aggregation. Actual national completeness depends on the original county WFS feeds.
- Original WFS endpoint: https://mapy.geoportal.gov.pl/wss/service/PZGIK/EGIB/WFS/UslugaZbiorcza
- The official [EPSG:2180 / PL-1992 CRS definition](https://epsg.io/2180) says its formal axis order is **northing, easting**. GeoJSON polygon coordinate pairs are, by contrast, **easting, northing**. Never infer a WFS BBOX argument axis order from a GIS screen coordinate pair.

## First-hand original source observations

A fixed **1,000 m × 1,000 m Warsaw centre** original-provider WFS 2.0 GetFeature was requested with COUNT=2 over public HTTPS.

| Original check | Evidence |
|---|---|
| Response format | GeoJSON FeatureCollection, name=budynki, declared CRS urn:ogc:def:crs:EPSG::2180 |
| Actual returned buildings | **Two** Polygon features at most per query; not a representative or complete census |
| Advertised attributes | ID_BUDYNKU, RODZAJ, KONDYGNACJE_NADZIEMNE, KONDYGNACJE_PODZIEMNE |
| Original polygon location | Two returned original polygons **intersect the physically intended Warsaw XY window**, when query BBOX uses EPSG-ordered northing/easting |
| Other result | A naive easting/northing BBOX returned two original polygons elsewhere, not in the intended Warsaw window |
| Source byte admission | None. Original source records, precise coordinates and source IDs are not committed or copied into this note |

**Critical error prevented:** In normal projected GIS XY notation the target rectangle has xmin=636500, ymin=486500, xmax=637500, ymax=487500 (metres in EPSG:2180). For this WFS 2.0 request the correct BBOX argument is **486500,636500,487500,637500,EPSG:2180**, because the WFS/CRS axis order is northing/easting. The incorrect 636500,486500,637500,487500 query returned geometries that failed the true Warsaw intersection check. Even with the correct request BBOX, the returned GeoJSON coordinate pairs remain ordinary easting/northing XY.

This is based on two observed source objects within one small spatial window. No official area-wide building counts, coordinate-independent control sites, building-part semantics or country-level accuracy established. The original response was inspected via public web retrieval; the newly added Python script has not itself been run against the live provider in this session.

## Reproducible bounded original-window tool

The [strict Python source-window probe](../../scripts/probe_pl_egib_warsaw_building_window_v0.py) hardcodes the original HTTPS provider, the building layer ms:budynki, EPSG:2180 and the target Warsaw 1 km rectangle; caps the result to two buildings and 256 KiB.

Explicit live invocation (no raw provider bytes written to disk):

~~~bash
python scripts/probe_pl_egib_warsaw_building_window_v0.py --live
~~~

Offline input of the actual original provider GeoJSON, stored **outside Git**:

~~~bash
python scripts/probe_pl_egib_warsaw_building_window_v0.py \
  --source-json /external/gugik/warsaw-two-original-buildings.json
~~~

The JSON receipt reports original response SHA-256, byte size, geometry intersection count, geometry type and only aggregate **nonempty field counts**. It prints no building IDs, attribute values or raw coordinates, rejects wrong location/CRS/schema, nonfinite or invalid polygon rings, too many rows and any redirect. It cannot make the model/insurer input admissible on its own.

Synthetic-only tests:

~~~bash
python -m unittest discover -s tests -p 'test_probe_pl_egib_warsaw_building_window_v0.py' -v
python scripts/check_all.py
~~~

## Next original provider checks

1. Re-run the exact live bounded probe and pin the anonymized receipt, preserving no original provider rows in the repository.
2. Compare a tiny original Warsaw window against the GUGiK EGiB national GeoParquet or regional GPKG release to quantify source time and ID reconciliation, source licence and geometry differences.
3. Validate building polygon topology, storey null rates, access rights, actual insurable asset meaning and duplication with EUBUCCO/Overture before any OpenCatastrophe exposure or TIV value is admitted.

The two observed polygons are evidence of **one working bounded original provider request**, not nationwide exposure readiness.
