<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dwd.cdc.lightning.monthly.v1.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dwd.cdc.lightning.monthly.v1.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dwd.cdc.lightning.monthly.v1.documented

## Source ids

- dwd.cdc.lightning.monthly.v1

**Provider:** Deutscher Wetterdienst / LINET (Nowcasting AG)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/BESCHREIBUNG_1c266171-e0fe-446e-b88c-43a508d900ad_de.pdf>

**Service root:** <https://opendata.dwd.de>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /climate_environment/CDC/grids_europe/monthly/lightning/density/LInumsum201307.nc.gz

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/gzip

**Format:** Monthly NetCDF4/HDF5 grids; July 2013 sample verified at 0.05 x 0.05 degrees, EPSG:4326, 1 x 201 x 221 (time, latitude, longitude); LInum (unit 1) and LIkA (kA)

**Scientific semantics:** Official product description (2025-10-02) and both sample file headers explicitly state CC BY 4.0 for the gridded product, not raw LINET. On 2026-11-24 a bounded HTTPS download of two July 2013 files succeeded via macOS, after Linux DNS failure. Original compressed bytes: https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/density/LInumsum201307.nc.gz (59485 bytes, SHA-256 2b6d5dfc1da8977e9a351dc2913cfd093c539bebde68b19911ff3224bfc320cf); https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/mean_amperage/LIkAmm201307.nc.gz (150582 bytes, SHA-256 d1e28898bc430c489bd4916b9a54dc90d1d3c82511f0d23a99adba872b2145da). Gzip integrity passed; h5py 3.16.0 and NumPy 2.5.5 read both HDF5 files. Both advertise CF-1.6, LIclim-Linet-v1, float64 data, fill/missing -0.01, and identical lat/lon/time arrays (time zero hours since 2013-07-01 00:00:00). All 44421 data cells finite and not fill in this sample; matching zero masks (11914 cells); 32507 positive count cells. LInum is integer-valued (0 to 672, sum 969164); LIkA ranges 0 to 5.998963253472441 kA. Pearson correlation of log1p(LInum) and LIkA over positive-count cells is 0.4297129826308147; this is descriptive, not hail validation. Method reference: https://doi.org/10.20944/preprints202502.1749.v2 (preprint), section 2, describes hourly summed amperage divided by hourly lightning count and then monthly averaging. Do not interpret LIkA as peak current or a monthly count-weighted mean; zero-current cells with zero count are not measured low-current strikes. Confirm exact current normalization, detection efficiency, network changes and missing-hour handling; never interpret missing coverage as zero hazard. Monthly data cannot reconstruct storm tracks, hail size or lightning jumps. Validate against independent radar hail climatology with held-out years and regions; compare count-only, ERA5-only and combined models. Original bytes remain outside Git; no database write, full-series test, formal rights or scientific approval, or admission.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** CC BY 4.0 in both original headers and official CDC terms; strong open-first priority. Exact sample pair verified, 228 months listed for each variable. Complete exact-product review, acquire paired months with hashes, preserve missing and zero-count masks. Raw LINET not covered.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/BESCHREIBUNG_1c266171-e0fe-446e-b88c-43a508d900ad_de.pdf>
- <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Notes:** Open-first qualification queue. CC BY 4.0 in both original headers and official CDC terms; strong open-first priority. Exact sample pair verified, 228 months listed for each variable. Complete exact-product review, acquire paired months with hashes, preserve missing and zero-count masks. Raw LINET not covered. Discovery/access only: no admission, no external bytes in Git, no model approval.
