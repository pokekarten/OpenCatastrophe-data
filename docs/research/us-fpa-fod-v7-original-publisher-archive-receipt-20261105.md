<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USFS FPA FOD seventh-edition: actually verified original metadata archive

**Observed 5 November 2026.** This is a *positive original-bytes receipt* for a 31,583-byte USFS metadata release ZIP plus a separately probed original **GPKG ZIP endpoint**. It is **not** a claim that the 238-MB source data archive, individual wildfire locations, source perimeters or hazard/loss calculations were downloaded or validated.

## Primary original publisher publication

- Official [Forest Service Research Data Archive page](https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.7)
- Version DOI [10.2737/RDS-2013-0009.7](https://doi.org/10.2737/RDS-2013-0009.7)
- Edition/title: Karen C. Short (2026), Spatial wildfire occurrence data for the United States, 1992–2024 [FPA_FOD_20260615], **Seventh Edition**.
- Publisher says government-funded data **can be used without additional permissions or fees**, with the stated citation to be used for reuse in research and other publications. The source metadata include **Access Constraints: None**. This general-use statement must not substitute for scientific hazard, event identity, loss/vulnerability, insurance portfolio, or source-specific CAT model approval.
- The immutable release reference is preferable to the mutable [CurrentEdition ArcGIS service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer).

## Verified original bytes (not just HEAD or publisher website text)

1. Official [RDS-2013-0009.7_Metadata_Fileindex.zip](https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/RDS-2013-0009.7_Metadata_Fileindex.zip).
2. Original server HEAD replied HTTP 200 with Content-Length **31,583**. Explicit complete 0–31,582 byte HTTP Range GET replied **206 Partial Content**, Content-Range **bytes 0-31582/31583**, and ZIP PK signature.
3. An original ZIP of **31,583** bytes was actually read. SHA-256 exactly equals the primary publisher's published **1e94a5cab0cdcf77ed92d3b5810dbe1960e704422363ee731367646ac9781a49**. All three source ZIP entries passed CRC:
    - _fileindex_RDS-2013-0009.7.html — 4,290 uncompressed bytes, SHA-256: 26c0039f0f3960a405ca8a492d999cb7c301f26f7e7f526758c2f2fc5cfd6bb8
    - _metadata_RDS-2013-0009.7.html — 107,109 uncompressed bytes, SHA-256: 79332a9da451489d733159a3a83b43cb776fdcc060aba4de5003f3e1b3c74b83
    - _metadata_RDS-2013-0009.7.xml — 62,911 uncompressed bytes, SHA-256: e1fd959e8c429cef4ba6c458e77840f95517b9656a0cf48cda9a00e27158ac14
4. Inside the publisher original ZIP, the file index names **FPA_FOD_20260615.gpkg** as the OGC GeoPackage distribution, implemented as a SQLite database with 1992–2024 wildfires. The original metadata reference a **Fires** table plus a separate NWCG agency/unit lookup and provide original provenance/field definitions.

This is the first **versioned, publisher-hash-verified original release metadata package** for this source in the project investigation. Only original file identifiers/hashes/aggregate metadata are documented; no original GIS asset bytes are added to GitHub.

## Full source data archive — reachable but NOT downloaded/verified

Official GPKG ZIP:
https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/RDS-2013-0009.7_Data_Format3_GPKG.zip

The actual server HEAD returned HTTP 200, **Content-Length 238,170,979 bytes**, and a byte-range 0–15 GET returned HTTP 206, **Content-Range bytes 0-15/238170979** with the ZIP magic header. Publisher catalog gives official SHA-256 **9e36ecd0d70dd5fa126be7b5ce5b02003867da04c41f3bd137f5ccdfca81b9b2**. The file's download accessibility is thus partially observed, but **its complete original bytes and SHA have NOT been verified**. Note that the full data ZIP is large (~227.14 MiB) and must not be accidentally committed.

## Executable fail-closed archive guard

The new offline checker consumes an operator-local original ZIP. It pins the **exact original metadata byte count, SHA-256, three allowed member names, ZIP CRC and release/citation/use-rights text**. Optionally, after a full authorized data ZIP download, it hashes all **238,170,979 bytes** in bounded 4-MiB blocks, requires the exact publisher SHA, inspects only the ZIP central-directory entry **Data/FPA_FOD_20260615.gpkg** and the first 16 SQLite header bytes. No event records, WGS84 coordinates or fire polygons are exported.

    python -m research_runners.us_fpa_v7_original_archive_receipt_v0 \
      --metadata-zip /private/RDS-2013-0009.7_Metadata_Fileindex.zip

    python -m research_runners.us_fpa_v7_original_archive_receipt_v0 \
      --metadata-zip /private/RDS-2013-0009.7_Metadata_Fileindex.zip \
      --data-gpkg-zip /private/RDS-2013-0009.7_Data_Format3_GPKG.zip

    python -m unittest tests.test_us_fpa_v7_original_archive_receipt_v0 -v
    python scripts/check_all.py

The second command is **prepared**, not claimed to have run successfully on the original GPKG. Even when both archives verify, separately review original GeoPackage tables/geospatial CRS and FPA-FOD source identity fields; reconcile actual archived 2024 marginal counts with the live [state × size MTBS-ID query analysis](us-wildfire-2024-state-size-mtbs-original-20261105.md); only then proceed to a physical event to MTBS footprint linkage and synthetic-exposure overlay.

**Never equate a technically authentic original file with a calibrated CAT model.** FPA is point-based historical wildfire reporting, not a complete independently sampled fire hazard, burned-severity footprint, insured-loss catalog or inward/outward treaty event set.
