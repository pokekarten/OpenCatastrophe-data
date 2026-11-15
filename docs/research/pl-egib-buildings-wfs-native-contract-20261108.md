<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Polish GUGiK EGiB Buildings WFS — bounded native metadata preflight (2026-11-08)

**Scope:** original-provider source contract and discovery only. No original provider XML fixtures, property polygons, insurer exposure or model admission in Git. Related European discovery [#1441](https://github.com/pokekarten/OpenCatastrophe-data/issues/1441) and research [#1448](https://github.com/pokekarten/OpenCatastrophe-data/issues/1448).

## Official primary sources

- GUGiK nationwide [EGiB documentation](https://www.geoportal.gov.pl/en/data/land-and-building-register-egib/).
- [GUGiK aggregation announcement of 16 July 2026](https://www.gov.pl/web/gugik/zbiorcza-usluga-wfs-dla-ewidencji-gruntow-i-budynkow-udostepniona-w-modulach-mapowych-serwisu-geoportalgovpl).
- **Original WFS**: https://mapy.geoportal.gov.pl/wss/service/PZGIK/EGIB/WFS/UslugaZbiorcza
- [Official EGiB GeoParquet and GeoPackage downloads announced 4 February 2026](https://www.gov.pl/web/gugik/budynki-z-egib-dostepne-do-pobrania-w-serwisie-wwwgeoportalgovpl).
- Original source record in [European research landscape](../../landscape/sources-europe-national-building-gaps-20261108.json).

The national WFS aggregates **385 county WFS endpoints** and collects changes daily **insofar as original county services publish them**. Service reachability alone does not establish national building completeness, historical stability or commercial permissions.

## Live native XML metadata observed on 8 November 2026

Three original public provider WFS requests were successfully made over HTTPS. The public web-fetching service returned the original XML, but original response bytes were NOT independently pinned and were not committed to the repository.

| Original operation | Native response | Scientific interpretation |
|---|---|---|
| **GetCapabilities WFS 2.0.0** | GUGiK provider; parcel layer **ms:dzialki**, building layer **ms:budynki**; building DefaultCRS **urn:ogc:def:crs:EPSG::2180** | Building WFS layer is advertised. Do not confuse parcels and buildings |
| **DescribeFeatureType, TYPENAMES=ms:budynki** | Declares **budynkiType**, **geom** GML SurfacePropertyType, optional string fields **ID_BUDYNKU**, **RODZAJ**, **KONDYGNACJE_NADZIEMNE**, **KONDYGNACJE_PODZIEMNE** | Schema presence does NOT prove a value for any actual building |
| **GetFeature, TYPENAMES=ms:budynki, RESULTTYPE=hits, COUNT=1** | WFS FeatureCollection, **numberReturned=0**, **numberMatched=1**, provider timestamp **2026-11-08T23:03:58** (provider time-zone interpretation unverified) | Constrained metadata response only. COUNT=1 is NOT a national building total |

**Not verified:** exact raw XML archive SHA, genuine building polygon bytes, national count, subcounty coverage, geometry validity, ID uniqueness, axis ordering, per-field missing rates, bulk commercial/redistribution licence, insurable TIV or carrier-level assets.

## Reproducible provider-contract script

The [native WFS metadata probe](../../scripts/probe_pl_egib_buildings_wfs_v0.py) hardcodes the original HTTPS endpoint, buildings layer, WFS 2.0.0 and EPSG:2180. Only three metadata-only requests are allowed; it does not support retrieving real building rows or polygons.

Explicit public live **metadata only**:

~~~bash
python scripts/probe_pl_egib_buildings_wfs_v0.py --live
~~~

Offline inspection of externally obtained **original XML** stored outside Git:

~~~bash
python scripts/probe_pl_egib_buildings_wfs_v0.py --offline \
  --capabilities-file /external/gugik/capabilities.xml \
  --schema-file /external/gugik/describe_buildings.xml \
  --hits-file /external/gugik/buildings_hits_count1.xml
~~~

The JSON report prints only provider metadata, known field *names*, source XML byte sizes and SHA-256 hashes and explicit **not-admitted / not-rights-cleared** flags. The three XML inputs are capped at 2 MiB each; DTD/entity declarations, exception reports, wrong CRS, wrong feature layer and feature-bearing hits responses are rejected. Off-provider redirects are blocked.

Test only synthetic XML fixtures:

~~~bash
python -m unittest discover -s tests -p 'test_probe_pl_egib_buildings_wfs_v0.py' -v
~~~

Repository checks:

~~~bash
python scripts/check_all.py
~~~

## Next provider-byte and modelling boundaries

1. Run the live metadata probe on an execution environment with connectivity. Preserve the output receipt only, not the third-party XML files. Note the exact execution time, rights and source version separately.
2. After source licence review, run a separately constrained bounded original GetFeature polygon sample with a real known-area BBOX; verify coordinates/axis ordering and building-part topology before using any geometry.
3. Quantify missing field rates, ID uniqueness, polygon validity and the county coverage gap. A successful WFS request alone cannot establish national completeness or building values.
4. Admit only via the separate source manifest/scientific review process; do not infer actual insurer portfolios, dwelling counts or insured total value from source metadata.

**This is not a source-admission, licensed data-ingestion or loss-modelling result.**
