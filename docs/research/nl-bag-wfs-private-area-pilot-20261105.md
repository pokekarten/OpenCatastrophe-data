<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BAG WFS 2.0: bounded server-side field projection and private usable-area QA

**Date:** 2026-11-05  
**Status:** Original-provider, bounded live evidence for **WFS privacy projection only**; aggregate research diagnostics. Neither original BAG feature bytes nor individual addresses/IDs/geometry nor original insurer records committed. No source admission or estimated insured value.  
**Existing BAG metadata:** `landscape/sources-european-building-registers.json` candidate `nl.kadaster.bag` (DO NOT register the same underlying BAG as a new independent exposure source).

## Primary official service verification

- Original [PDOK BAG WFS 2.0 service](https://www.pdok.nl/ogc-webservices/-/article/basisregistratie-adressen-en-gebouwen-ba-1): `https://service.pdok.nl/kadaster/bag/wfs/v2_0`.
- Original `DescribeFeatureType` metadata query `?service=WFS&version=2.0.0&request=DescribeFeatureType&typeNames=bag:verblijfsobject`: XSD was retrieved successfully (`application/gml+xml; version=3.2`); `verblijfsobjectType` has `identificatie:string`, `oppervlakte:long`, `status:string`, `gebruiksdoel:string`, `pandidentificatie:string`, and additional address properties (`postcode`, `huisnummer`, `openbare_ruimte`, `woonplaats`). The WFS **single** `pandidentificatie` field must not be mistaken for the newer BAG OGC API v2's **array** of referenced `pand` objects. See [PDOK BAG v2 announcement](https://www.pdok.nl/-/nieuwe-bag-ogc-api-features).
- Verified **server-side selected attribute projection**: `GetFeature` with `propertyName=identificatie,oppervlakte,pandidentificatie,status,gebruiksdoel`, bounded `count`, `outputFormat=application/json` and EPSG:28992 bbox returned **exactly those five attribute fields** in JSON, excluding `postcode`, `huisnummer` and address descriptors. The GeoJSON still includes `Point` geometry and source record IDs, which must remain private; only counts and aggregates may leave the private processing boundary.
- A CSV format probe did not return a usable response; do not assert that the provider supports field-projected CSV until proven. Likewise, previous `properties=` attempt against BAG OGC API v2 did not prove safe projection; only the independently verified **WFS PropertyName request** may be used for this pilot.

### Minimal real-provider bounded evidence receipt (no raw source rows)

Approximate urban research window, CRS84 `5.1202,52.0902,5.1206,52.0906` transformed by PostGIS EPSG:28992 to a bounded WFS RD New request bbox `136701.28,455804.71,136728.86,455849.32,EPSG:28992`. The query explicitly requested only the five safe WFS fields above and `count=50`.

| Source observation | Aggregate result | Interpretation |
| --- | ---: | --- |
| WFS `numberMatched` and returned usable-area units | **8 / 8** | Complete bounded sample, no continuation or truncated count |
| Units with `status=Verblijfsobject in gebruik` | **8** | Observed unit lifecycle status in selected subset |
| Sum of the eight `oppervlakte` observations | **767 m²** | BAG **usable unit area**, not building gross floor or construction volume |
| Distinct **singular** WFS `pandidentificatie` references | **5** | WFS-only building reference, not the BAG v2 complete multi-`pand[]` relationship |
| WFS unit singular pand references found among separately retrieved 21 BAG `pand` IDs in same small source bbox | **8 / 8** | Strong official source-ID consistency, but not proof of all links or insured ownership |
| Valid returned field projection | **5 safe property keys** | No address-field names in returned feature properties |

**Caveats:** Sample is a tiny convenience window, not representative of Dutch residential stock. Source-use categories were heterogeneous, including pure residential, mixed commercial/residential, industrial/retail and accommodation functions. Thus **all 767 m² cannot be priced as residential replacement cost**. Never infer cadastral title, apartment/household count, insurance penetration, building-volume m³, parcel ownership or individual risk exposure from this aggregate.

## Safe research implementation

`scripts/audit_pdok_bag_wfs_private_area_v0.py` and `tests/test_audit_pdok_bag_wfs_private_area_v0.py` provide a strictly bounded **offline, no-network, no-DB-write** auditor for *privately obtained* original projected WFS GeoJSON. Every request must:

1. Target exactly the HTTPS PDOK WFS 2.0 verblijfsobject endpoint with only `service`, `version`, `request`, `typeNames`, `count`, `outputFormat`, `propertyName`, `bbox`; all five property names must match the safe allowlist. Limit ≤100 records, EPSG:28992 extent ≤1000m by ≤1000m.
2. Return the expected RD New CRS, `name=verblijfsobject`, `numberMatched == feature_count`, complete page, exact non-address field set, unique unit IDs, bounded valid whole-m² usable area, valid status/use and expected point geometry within the requested bbox. Reject any extra address field, duplicate ID, malformed geometry, missing/partial response, larger source window or changed API semantics.
3. Be read from a **private file outside the repository**. The output retains neither per-unit IDs nor coordinates/pand IDs/individual areas, nor even the approved original bbox, only coarse aggregate counts/areas, explicit source-rights uncertainty and `complete_multi_pand_links_verified=false`.
4. Apply a **minimum five in-use-unit threshold** before publishing aggregate area or counts. Suppress use-category cells with fewer than five records. A zero-building/zero-unit sample yields suppressed/undefined metrics, not proof of no property risk.

Use only with a source-terms-reviewed, privately stored bounded JSON response, preserving the actual URL as an explicit input argument:

```sh
python -m unittest tests.test_audit_pdok_bag_wfs_private_area_v0 -v
python scripts/audit_pdok_bag_wfs_private_area_v0.py \
  --input /private/bag-wfs-bounded-projected.json \
  --source-url 'https://service.pdok.nl/kadaster/bag/wfs/v2_0?service=WFS&version=2.0.0&request=GetFeature&typeNames=bag:verblijfsobject&count=50&outputFormat=application/json&propertyName=identificatie,oppervlakte,pandidentificatie,status,gebruiksdoel&bbox=136701.28,455804.71,136728.86,455849.32,EPSG:28992'
python scripts/check_all.py
```

**Admissibility boundary:** This audit does NOT add true building-level usable area to the exposure DB, infer a full multi-pand linkage or value any building. Validate multi-pand relationships from an appropriately field-restricted 2026 OGC API v2 path or a duly authorised private extractor with independent linked-ID consistency and use-class validation. CBS cost indices and private insurer pricing-method candidates from PR #1347 are not base replacement-cost values. Original WFS feature geometry and identifiers must never be published in this repository.
