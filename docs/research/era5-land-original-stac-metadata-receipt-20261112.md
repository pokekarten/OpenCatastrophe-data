<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ERA5-Land original public STAC metadata: rights and execution receipt — 2026-11-12

**Scope:** one exact *public collection metadata* JSON response for
`copernicus.c3s.era5-land`. The original provider is ECMWF / Copernicus C3S:
`https://cds.climate.copernicus.eu/api/catalogue/v1/collections/reanalysis-era5-land`.
The bytes were read on **2026-11-12** via unauthenticated, read-only
third-party HTTP transport and immediately reduced to a non-sensitive
metadata-only research summary. No meteorological data values, GRIB,
NetCDF, job outputs, signed URLs or credentials were accessed.

## Exact source-response identity and Neon research checkpoint

- Original retrieved JSON response body: **5,537 bytes**, `Content-Type:
  application/json`. SHA-256:
  `9cb5b77cfed967401d374eafcb4f9799f771cf53e1350aa18e20ffca8c0e2016`.
  This is a hash of **that response**, not a universal/version-stable
  original dataset hash, model artifact or cryptographic proof of provider
  authenticity. The catalogue is mutable and its `updated` field was
  `2026-11-12T00:00:00Z`.
- STAC `Collection`, id `reanalysis-era5-land`, `stac_version=1.1.0`,
  original self-link, original `license=CC-BY-4.0`, and DOI
  `10.24381/cds.e2161bac`. Publisher-declared global bbox uses the
  original **0–360 longitude convention**:
  `[0.0,-89.0,360.0,89.0]`. Treat it as an advertised source envelope,
  *not* a precise grid map or guarantee of exact coastal coverage.
- STAC temporal start: `1950-01-01T00:00:00+00:00`; endpoint availability
  is mutable. The dataset is an **hourly, land-only model reanalysis**,
  not independent observed extreme-event measurements. Original CDS
  [dataset page](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land)
  advertises a 0.1-degree grid and approximately 9-km native resolution.
  This is not building-level exposure or flood inundation.
- Source **commercial licence**: the product-specific original catalogue
  declares [CC BY 4.0](https://spdx.org/licenses/CC-BY-4.0); commercial
  data reuse with attribution is allowed. **Retrieval access is separate**:
  actual data download or ARCO access must follow the
  [CDS account/API-token and dataset-terms acceptance flow](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download).
  The anonymous STAC collection response alone does **not** authorize
  a credential-free or unrestricted automated GRIB/NetCDF download.
- **Actually inserted:** insurance-risk-core Neon
  `research.source_sample_v0.sample_id=35`,
  `sample_kind=public_metadata`, original-response SHA-256 as above,
  canonical JSONB sample hash
  `ec482d4a4a01a19579bdb66a703d60e17f5762383f75f140949917c9febead22`.
  The external source bytes were *not* persisted in Neon or Git.
  Canonical source candidate `actual_sample_state` advanced from
  `not_collected` to `metadata_only`; its narrower commercial
  `allowed_verified` verdict remains source-scoped. It remains
  `admission_status=not_admitted`.

## Executable offline replay contract

`scripts/era5_land_stac_metadata_preflight_v0.py` inspects one locally
obtained **at-most 16,384-byte STAC JSON response** with fixed source ID,
license link, DOI, STAC self-link, original spatial/temporal envelope,
and publisher sanity signal. It rejects duplicate JSON keys, unbounded
inputs, malformed/overflow numbers and wrong product/licence identity.
The script fetches **zero** URLs; it returns only bounded metadata,
source-body SHA-256 and explicit negative science/admission fields.
Its focused regression tests are synthetic-only.

Example (metadata JSON must already have been lawfully obtained outside Git):

```sh
python -m unittest tests.test_era5_land_stac_metadata_preflight_v0 -v
python -m scripts.era5_land_stac_metadata_preflight_v0 --input /private/era5-land-collection.json
```

Read-only research sample verification:

```sql
SELECT sample_id,source_id,sample_kind,provider_response_sha256,
       sample_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
         AS sample_hash_ok,
       sample_json->>'original_response_bytes' AS original_stac_bytes,
       model_input_approved,source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id=35 AND source_id='copernicus.c3s.era5-land';
```

## Strict outstanding scientific and technical gates

**Not acquired:** any ERA5-Land temperature, rainfall, wind, runoff,
soil-moisture or other reanalysis **value**, native GRIB/NetCDF bytes,
temporal event series, regional clipping, or calibrated loss estimates.

A consumer must first obtain a valid, permitted CDS account/API token and
dataset terms acceptance, choose a bounded immutable variable/space/time
slice and freeze raw-output byte identity, **units/accumulation semantics**,
UTC time resolution, missing values, spatial representativeness and
independent out-of-sample validation. ERA5-Land cannot be counted as an
independent historical loss observation, insured building, ground-truth
rainfall station, vendor CAT catalogue or OEP/AEP loss model. Keep
`model_input_approved=false`, `research_only=true`.
