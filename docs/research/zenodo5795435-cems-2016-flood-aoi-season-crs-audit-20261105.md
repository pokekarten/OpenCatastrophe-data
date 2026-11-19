<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Actual original Zenodo Geo-Harmonizer CEMS AOI index: 2016 Loing source gap and year/CRS audit

**Reviewed live 2026-11-05.** The archive's **203,733 original UTF-8 bytes** were fetched from the publisher endpoint into a bounded read-only research session and parsed: **455 point features**, exact published record id, licence, CRS, EMSR165 subset and year anomalies examined. A standalone JavaScript MD5 implementation was self-tested against the standard `abc` digest before hashing the retrieved original UTF-8 source text in memory. **Calculated MD5 = `cda186323fe76195b183316fd06c2547`, EXACTLY matching the publisher's original asset checksum**, with exact matching length **203,733 bytes**. **No original data were committed to Git, saved durably as a local source artifact or imported into any production/insurance model database.** This verifies the retrieved index's published checksum, not original satellite imagery rights, source AOI record correctness or access to separate restricted CEMS products.

## Primary archive, licence and exact reproducible source receipt

Published independent research dataset: [*Copernicus EMS flood activations delimitations (2012–2020), rasterised at 30 m and aggregated per year and season*](https://zenodo.org/records/5795435), Codrina Maria Ilie / Geo-Harmonizer, DOI **10.5281/zenodo.5795435**, version v1, CC BY 4.0 as declared in its [original record JSON](https://zenodo.org/api/records/5795435). This is a **derived Copernicus Rapid Mapping product**; record-level CC BY 4.0 requires attribution and does **not** grant rights to all independent underlying commercial satellite images or the separate restricted EMSN028 Risk & Recovery products.

| Actual publisher asset | Reported original bytes | Published MD5 | Scientific role |
| --- | ---: | --- | --- |
| [Original AOI index GeoJSON](https://zenodo.org/api/records/5795435/files/clm_flood.events_copernicus.ems.geojson/content), name \`clm_flood.events_copernicus.ems.geojson\` | **203,733** | \`cda186323fe76195b183316fd06c2547\` | Points identifying selected Rapid Mapping activation AOIs, **not flood polygons** |
| [2016 spring COG](https://zenodo.org/api/records/5795435/files/clm_flood.events_copernicus.ems_p_30m_0..0cm_20160301..20160531_eumap_epsg3035_v0.2.tif/content) | **277,916,484** | \`5a980fa481ac53d75e5d8397461a8cda\` | **Seasonal** 30 m European raster mosaic: 1 March–31 May |
| [2016 summer COG](https://zenodo.org/api/records/5795435/files/clm_flood.events_copernicus.ems_p_30m_0..0cm_20160601..20160831_eumap_epsg3035_v0.2.tif/content) | **278,041,114** | \`1b0d406735e5692652df915b9dce7c8b\` | **Seasonal** 30 m European raster mosaic: 1 June–31 August |

The record describes \`GeoTIFF\` clouds optimized, projection **EPSG:3035**, type **signed int16**, value **100 for flooded pixels** and **255 for nodata**. Other raster values, nodata masking at particular locations, actual event-specific timestamp, original vector topological quality, provider licences and maximum depth have **not been independently inspected**; do not infer that every non-100 pixel is physically dry. The two large raster bytes were **not downloaded**, and their MD5s are **publisher-declared only**.

## Actual parsed GeoJSON index and the critical geographic finding

Original file structure: \`FeatureCollection\`, root \`name="clm_flood"\`, a legacy GeoJSON \`crs\` object with exact \`urn:ogc:def:crs:EPSG::3035\`, and **455 \`Point\` features**. Its coordinates are *projected ETRS89 / LAEA metres*, e.g. Paris EMSR165 point **[3760184.0514, 2890959.4050]**, **not geographic longitude/latitude**. This is not WGS84-compliant **RFC 7946** GeoJSON despite its filename. Importers that silently assume WGS84 must be blocked; explicit EPSG3035 handling is mandatory.

Actual original \`EMSR165\` rows – all assigned to **\`spring\`**, 2016, raster \`...20160301..20160531...tif\`:

| \`EMS_AOI\` (source spelling) | \`EMS_ID\` | Derived AOI coordinate kind | CEMS index season |
| --- | --- | --- | --- |
| \`POISSY\` | \`EMSR165\` | EPSG:3035 point | Spring 2016 |
| \`MANTESLAJOLIE\` | \`EMSR165\` | EPSG:3035 point | Spring 2016 |
| \`PARIS\` | \`EMSR165\` | EPSG:3035 point | Spring 2016 |
| \`YERRES\` | \`EMSR165\` | EPSG:3035 point | Spring 2016 |

**No Montargis-named AOI point** occurs in the entire parsed original index; **no EMSN028** occurs in it either, as it is **Rapid Mapping-only**. The [official EMSR165 activation](https://mapping.emergency.copernicus.eu/activations/EMSR165/) currently reports **8 AOIs and 21 products**. The derived index contains only **4 of those activation AOIs**, and no provider evidence here establishes whether its missing four should overlap Montargis. Do **not** interpret these four index points as complete 2016 flood footprints or eight independently observed catastrophe events.

For contrast, the separate [official **EMSN028** Risk & Recovery activation](https://mapping.emergency.copernicus.eu/activations/EMSN028/) **does** list an **Observed Flood Extent (Detail): Montargis** and a separate Maximum Flood Extent product for Montargis. Its published detail map is named \`EMSN028_15MONTARGIS_01OBSFLOODEXTENT_DETAILS_v1_100dpi.pdf\`. Its text says the **31 May–9 June 2016 observed flood extent is a multi-image composite**, with Sentinel-1A (31 May and 4 June), Radarsat-2 (2 and 4 June), Cosmo-SkyMed (3 June), and optical data on 9 June, with weaker thematic reliability near urban/wooded areas. The original map prominently marks **RESTRICTED USE** and says access is restricted to authorized end users with contact \`ems-risk-recovery-mapping@jrc.ec.europa.eu\`. Our review attempted the official PDF screenshot but the previously indexed signed preview had expired; the **separate printed legend and product policy must be reverified through fresh authorised provider access before any original EMSN028 GIS acquisition or redistribution**. Do not bypass sensitivity flags or assume CC BY of Zenodo's *other dataset* overrides the EMSN028 access restriction.

## Data quality flaw independently identified in the published 455-index entries

We checked every \`YEAR_START\` against the first year encoded in its related seasonal GeoTIFF filename. **13 entries conflict**:

| Activation | Number of affected AOI points | Indexed \`YEAR_START\` and \`YEAR_END\` | Referenced mosaic name |
| --- | ---: | --- | --- |
| \`EMSR441\` | 7 | 2000 | \`20200601..20200831\` |
| \`EMSR442\` | 4 | 2000 | \`20200601..20200831\` |
| \`EMSR445\` | 2 | 2000 | \`20200601..20200831\` |

The exact source metadata state **2000**, yet the filename points to **summer 2020**. We **do not change YEAR_START to 2020 on assumption** and do not count these as physical floods in 2000 or 2020. Source file issue/temporal join must be reconciled with official activation and original imagery before frequency modelling. The bounded audit contains these as **explicit known anomalies**, but blocks any additional unreviewed mismatch or unknown source revision.

The original file has **6 total 2016 spring AOI points** and **13 total 2016 summer AOI points** (not independent flood-event counts). Although EMSR165 was activated on 1 June, this derived index assigns the four EMSR165 points to **spring**, plausibly using the start of the flood rather than the activation date; the underlying season assignment method must be checked. A June-only raster query will **silently omit** these four source AOIs; adding both seasonal raster mosaics is **not** a valid way to isolate a single 2016 event, since they combine several activation footprints and months.

## Implemented admission gate (no original archive bytes in Git)

[Strict original-index validator](../../research_runners/zenodo5795435_emsr165_aoi_original_index_v0.py) checks an **exact 203,733-byte file and publisher-pinned MD5** before loading it. It then requires the exact EPSG3035 legacy CRS, source index identity, selected four EMSR165 AOI names, year/season/raster filename mapping, all 455 source rows and exactly 13 known year conflicts. Unexpected event products, changed source years, spoofed \`MONTARGIS\` AOI, fake WGS84 coordinates, unknown years or source-shape changes **fail closed**. Even when source MD5 matches, a local receipt is **not** a complete guarantee of third-party imagery rights, GIS flood extent, independent 2016 holdout or usable risk-model input.

[16 synthetic offline tests](../../tests/test_zenodo5795435_emsr165_aoi_original_index_v0.py) cover the identity, projected CRS, four AOIs, unknown/risky years, 2000-vs-2020 anomalies, wrong event family, protected model admission and unverified original-source digest.

Reproduce after **permitted source download outside Git**:

\`\`\`sh
python research_runners/zenodo5795435_emsr165_aoi_original_index_v0.py \
  --original-geojson /local/clm_flood.events_copernicus.ems.geojson
python -m unittest discover -s tests -p 'test_zenodo5795435_emsr165_aoi_original_index_v0.py' -v
python scripts/check_all.py
\`\`\`

The source and its record-level licence are catalogued as **research-use candidate**. The validated **index** may eventually help locate an appropriately licensed flood-raster subset and source AOI, but its present content is **not** a Montargis-specific measured maximum flood extent, asset inundation depth, or regional OEP/AEP frequency claim.

## Next causal step

For Montargis 2016, the best spatially matched source remains **EMSN028 AOI15** **if** its rights and geodata access can be legitimately cleared. Alternatively obtain DDT45 original event-specific 2016 AZI ZIP/ZICH and the mark-inclusion lists of DRIEE2017/DDT2021. Do not train on the same 68 marks used to reconstruct the published atlas, do not conflate 2023 PPRI hazard with 2016 field truth, and do not use a 30-m seasonal merged mask as a building-depth measurement.
