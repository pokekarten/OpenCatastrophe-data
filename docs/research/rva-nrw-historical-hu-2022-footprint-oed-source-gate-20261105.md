<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW historical HU 2022: official building footprint source for fictional R+V OED

**Reviewed 2026-11-05. Publisher index identified and verified in browser; original ZIP (859.3 MB displayed) not downloaded, no original building feature imported, and no R+V insurer-specific exposure inferred.**

## Precise official source target

Official publisher directory:
https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/

Full original 2022 archive URL listed by publisher:
https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip

The publisher HTML directory explicitly identifies:
- 2016 through 2022 annual historical source ZIPs;
- 2022 ZIP shown as **859.3 MB** (display only, **no independently measured file byte count or full-source SHA-256**);
- **EPSG:4647** as source CRS, **not WGS84**;
- **Datenlizenz Deutschland – Zero – Version 2.0** for this *specific directory*. Broader NRW ministry prose may use BY 2.0 for other layers; keep exact asset-level licence review distinct.

Original metadata catalogue: https://data.gov.de/suche/daten/historische-hausumringe-nw . AdV-MIS discovery also links the official archive at https://www.distributions.informationgrid.eu/freitextsuche?q=Amtlicher+Gemeindeschl%C3%BCssel .

The historical Hausumringe dataset describes over **10 million** physical building/structure outlines in NRW; may include non-residential industrial structures and other surface-built objects. AGS is available; original object identifier, function code and update date are described as available since 2020. They are not actual insurer assets, policy locations, living-space-only buildings or rooftop PV/roof attributes.

Research-only bounded official index probe: research_runners/rva_nrw_hu_2022_original_index_receipt_v0.py . With --live it downloads only the small HTML index; validates ZIP basename/link, declared vintage, CRS, displayed size and directory-specific rights; computes full index HTML SHA-256; **does not request ZIP or any feature row**. No original ZIP checksum or CRS geometry transform is claimed.

## Why the original 2022 HU matters

For our already source-reviewed synthetic R+V Allgemeine solo 2025 53-Kreis NRW OED experiment, this is a more temporally matched **physical building-location candidate** than a later-version Overture global building layer. There are still distinct time bases:

1. 2022-05-15 original Zensus 53-Kreis aggregate: **4,042,220 buildings with living space**, including mixed residential use;
2. official *historical* HU 2022 archived physical building/structure footprint, not necessarily sampled 2022-05-15 and broader structural population;
3. 2025 R+V Allgemeine solo **1,060,546 national year-end connected-building contracts**, national building HGB annual written premium EUR 997.710 million;
4. secondary MaStR-derived 2026 **876,684 registered NRW building PV generating units**, not unique roofs or insured PV sites.

The existing full nationwide 400-Kreis uniform-fictional R+V allocation has **214,808 hypothetical NRW contracts**; this is a mathematical conditional model output, not a true R+V NRW contract total. The 10,000 NRW per-scenario pilot must not be scaled into a full insurer financial loss curve.

## Required source → geocoded OED stage

1. In a source-controlled offline compute environment, acquire the **exact official original** ZIP, record complete bytes/SHA-256, validate ZIP central directory, path traversal/compression bomb limits, required SHP/SHX/DBF/PRJ, encoding, source CRS, geometry and field types. Metadata receipt alone is insufficient.
2. Preserve source German municipality AGS **leading zeros**, original building/structure-function code, object ID and the source date/geometry vintage. Audit function-class definitions independently; exclude unverified non-residential objects and do not force HU physical population to equal living-space-only census count.
3. Crosswalk 2022 municipality AGS to 53 five-character NRW Kreis IDs and verify independent county boundary vintage. Do not silently assign unknown or ambiguous border objects; keep duplicate and source lineage controls.
4. Reproject **EPSG:4647 → EPSG:4326** via separately tested pyproj/PROJ with correct axis convention; compute an interior point from real polygons only after CRS, topology, NRW bounds and area tests. County centroid is **not** an individual risk location.
5. Separately select and sample **fictional** insurer contracts from eligible physical candidates, with stable seeds and transparent propensities and source/evidence receipts; prohibit any real R+V insurer-site claims, addresses, customer details, exact premium/TIV inference, or unsupported PV insurance attribution.
6. Only after a verified wind vulnerability mapping, individually justified hypothetical replacement values, defensible financial terms and hazard/event catalogue can Germany Oasis native GUL→IL→RI and OEP/AEP be tested. Official OED CSV schema compliance is not hazard/model compatibility.

**No provider original ZIP was downloaded or stored in Git/Neon during this change.**

Reproduction:
- python -m unittest discover -s tests -p test_rva_nrw_hu_2022_original_index_receipt_v0.py -v
- python research_runners/rva_nrw_hu_2022_original_index_receipt_v0.py --live

No live index response should ever be presented as the original ZIP-byte SHA-256.


## Follow-up: bounded original ZIP header, EOCD and central directory probe

An additional source-aware probe is now implemented in
research_runners/rva_nrw_hu_2022_original_zip_range_receipt_v0.py .
It requests **HEAD** from exactly the pinned official 2022 ZIP and, **only
when the provider returns a true HTTP 206 with the expected Content-Range**,
downloads at most ~65 KiB from EOF and at most 1 MiB for the ZIP central
directory. It rejects absent/ambiguous end-of-central-directory signatures,
unsupported multidisk/ZIP64 structures, path traversal, invalid central
signatures, missing SHP/SHX/DBF/PRJ members, duplicate names and oversized
metadata. The script does not read full geometry, DBF rows, or individual
insured policy sites. Original ZIP **full SHA-256 is still unverified**, and a
ZIP header/footer by itself cannot prove member integrity.

Run locally **only on an explicitly authorised machine** after reviewing
the original source URL and bounding the network requests:

- python -m unittest discover -s tests -p test_rva_nrw_hu_2022_original_zip_range_receipt_v0.py -v
- python research_runners/rva_nrw_hu_2022_original_zip_range_receipt_v0.py --live

A separate [bounded original-source workflow](../../.github/workflows/rva-nrw-hu-2022-source-index.yml)
runs negative fixtures, official source directory listing preflight and this
exact optional historical archive metadata probe. If source byte ranges are
unsupported, the probe should remain **BLOCKED**, rather than downloading the
entire ~859 MB ZIP as a fallback.

Do not conflate an HTTP Content-Length with a full SHA-256 receipt.
