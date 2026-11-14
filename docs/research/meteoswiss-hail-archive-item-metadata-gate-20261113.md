<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MeteoSwiss hail climatology — one STAC Item sample, archive transport blocker and 2026 COG migration

**Date:** 2026-11-13. **Status:** research metadata only, no hail raster observation values or CAT model input.

## Why the original collection metadata is not enough

MeteoSwiss [official hail climate Open Data documentation](https://opendatadocs.meteoswiss.ch/c-climate-data/c5-radar-based-climate-data)
identifies the public STAC collection
`ch.meteoschweiz.ogd-radar-derived-grid`, DOI
`10.18751/Climate/Griddata/CHHC/1.0`, Swiss LV95 / EPSG:2056
and source credit `Source: MeteoSwiss`. The monthly/yearly source items
and **`archive-ch`** are distinct: historical products and HailStoRe-derived
return-value hazard maps reside in the archive. The April–September
season constraint is a data-generation rule, not proof of zero hail
during the remaining months.

**Important 2026 source format update:** the [FSDI July 2026 release notes](https://docs.geo.admin.ch/releases/release-notes.html)
and [Swiss data-release notice](https://www.geo.admin.ch/en/new-data-01072026)
state that hail hazard assets are now offered as **COG GeoTIFF** as well
as NetCDF in this collection. An earlier NetCDF-only source expectation
would miss potentially suitable raster tiles. However an available
GeoTIFF/COG format alone does not validate actual pixel values,
return-period definitions, CRS, uncertainty or licence of a specific
archive asset. The [official July 2026 hail hazard announcement](https://www.geo.admin.ch/de/datensatz-06072026)
links directly to the `archive-ch` STAC item.

## Independently checked original metadata and private research receipts

Two individually bounded public STAC metadata GETs were actually
performed through an external source-reading intermediary on 2026-11-13.
The original response bytes provided by the intermediary were transiently
hashed in private research Neon. Original bodies and provider-returned URLs
were not persisted in the repository or private research sample table.

| Exact official metadata request | Verified body size | SHA-256 of source body | Neon research sample |
| --- | ---: | --- | --- |
| [Exactly one STAC item](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid/items?limit=1) | **2,001 bytes** | `432bd6fa794662bcaaa111153479bda988c8ac1d9513bd1c80664d543fe4d3a1` | **#71** |
| [The returned item 202510-ch](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid/items/202510-ch) | **1,170 bytes** | `a49ae306ef988cc1894ba538028caf2b6206b15c7308b29675147b6c12a6ecbf` | **#72** |

Both resulting private `research.source_sample_v0` rows are
`research_only=true`, `model_input_approved=false`,
`source_byte_persistence_authorized=false` and contain no raw provider
body. Independent, non-GitHub source API observations are indexed as
`research.source_api_smoke_receipt_v0` IDs **#18 and #19**.
The strict GitHub-reviewed 18-source runner has **not** executed
either request, and no live metadata response is accepted as proof
of original NetCDF, COG or GeoTIFF bytes.

The first returned item `202510-ch` has **zero linked assets** in
its separately fetched detailed metadata. Its displayed title
`CH at 10.2025` and metadata `datetime=2026-10-31T04:00:18.859934Z`
do **not** independently establish a consistent source-vintage/date
relationship. Treat this item as an **unsuitable data-value candidate**,
not as evidence that the collection or `archive-ch` contains no assets.
The one-item listing is not a complete collection inventory.

## Independent archive-ch source-reading limitation

A separately attempted read of the exact
[official archive-ch STAC Item](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid/items/archive-ch)
returned a response representation whose nominal decoded size
was about **59 KiB**, but the intermediary representation could
**not** be reconstructed byte-for-byte and the hash/JSON validation
therefore **failed closed**. No archive original-body SHA, asset count,
media-type inventory or model-ready download is claimed. Do not
interpret this as a definitive provider API failure.

To overcome the intermediary representation limit without unrestricted
provider crawling, `scripts/probe_meteoswiss_hail_archive_item_v0.py`
implements one hardcoded metadata-only `archive-ch` GET:
- no user-supplied URL or other free-form request parameters;
- at most **131,072 bytes**, **30 seconds**, **zero redirects/retries**;
- strict UTF-8 JSON, exact collection/item identity, at least one
  provider asset metadata object, and bounded MIME/count-only evidence;
- no follow-up asset links, original payload dumps or automatic
  NetCDF/COG/GIS file downloads; original source body SHA-256 is emitted,
  not the source body itself;
- manual `--live` opt-in only, no scheduled polling.

Synthetic negative/positive tests are in
`tests/test_probe_meteoswiss_hail_archive_item_v0.py`, with
`.github/workflows/meteoswiss-hail-archive-metadata.yml`
configured for **offline PR tests** and a **separate manual
`workflow_dispatch` restricted to trusted `main`**. This new
single archive metadata job does **not** expand the existing
18-reviewed capability allowlist, modify the existing Collection-only
source-access contract, or grant broader asset rights.

## Legal and scientific gates

MeteoSwiss public Open Data terms specify **CC BY 4.0** with
source attribution. FSDI API terms allow free, registration-free
use but prohibit excessive automated service requests under fair-use
conditions: [MeteoSwiss rights](https://opendatadocs.meteoswiss.ch/general/terms-of-use),
[FSDI fair-use terms](https://www.geo.admin.ch/en/general-terms-of-use-fsdi).

Before a true hail hazard source-data sample or OEP/AEP model
calibration, require separate verification of:
1. the exact `archive-ch` Item and a chosen return-period asset's
   immutable source URL, media type, version, byte size and original SHA-256;
2. native COG/NetCDF grid/CRS/NoData/units, return period, MESHS
   versus LEHA spatial reference area and HailStoRe model uncertainty;
3. appropriate source attribution/reuse terms and internal
   dataset/asset licensing, no unexpected link-target redirects;
4. independent scientific validation and explicit model-input
   approval, still **false**.

No original data files, human location records, insurer exposure,
claim data or CAT model results were admitted by this research step.
