<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg 2025 solar roof-facet WMS: original service access and metadata probe

**Research date:** 2026-11-01. **Non-admission, no original roof, address or person records.**

## Product-specific evidence and source differences

In the original **September 2025 tetraeder.solar documentation** for the Klima-Agence solar potential source (<https://download.data.public.lu/resources/potentiel-solaire-au-luxembourg/20251003-115312/dokumentation-datenexport-wms-luxemburg-20250904.pdf>, especially pp. 3–4), a WMS base URL is documented:

`https://mapproxy.tetraeder.solar/st_luxemburg_25/service?`

The document lists distinct:
- **Building layer**, attributes `hid`, PV/ST eligibility and estimated energy/potential features;
- **Roof-facet ('Dachteilflächen') layer**, attributes `tilt` in degrees, `aspect` in degrees (zero = North), `area3d` in square metres, `flat` 0/1, solar radiation/potential and other energy values;
- **Irradiance clustering** and **2020 original-model estimation of existing PV/ST installations**, which is NOT a verified present-day PV equipment registry.

The document also says the service **uses access credentials from an older project WMS**; it does **not** say that we have these credentials or that all WMS content can be bulk copied.

Merged PR #951 observed the original 2025 **building SHP-linked DBF** metadata: 238,433 rows *declared in header*, 12 columns, `hid` and `pv` but **no `tilt/aspect/flat/area3d`**. A separate WMS is required for roof facets. That original header evidence is not individual roof attribute evidence.

## What this PR actually tests

`research_runners/lu_solar_wms_capabilities_v0.py` parses a **bounded public WMS GetCapabilities XML only**, retaining named layer metadata, advertised queryable state and GetFeatureInfo MIME formats. Strict size and XML safety checks reject DTD/entities, malformed service exceptions, excessive layers and misleading responses. All tests use entirely synthetic XML.

`.github/workflows/luxembourg-solar-2025-wms-capabilities.yml` attempts **one exact official endpoint**, read-only `GetCapabilities` over HTTPS, max 2MB / max 50 seconds / zero retries / no credentials or address queries. It never issues `GetMap`, `GetFeatureInfo`, WFS `GetFeature` or downloads original polygons.

- If HTTP 401/403, network rejection or other unavailable public endpoint: report **BLOCKED**, do not claim a successful facet data read. The background synthetic tests can still pass.
- If HTTP 200 contains real WMS capabilities: report only layer names and advertised operations; **this still does not prove real WMS `GetFeatureInfo` works, available roof facet attributes, downloadable geometry or reuse rights**.
- If HTTP 200 contains HTML login or non-WMS XML: fail closed.

WMS is typically a **rendering and point-query service**, not a general open bulk geospatial data download contract. A source field described in a vendor PDF is not automatically accessible for independent per-building attribution. `HID` is vendor-local, not an ACT or EUBUCCO ID.

## Real anonymous original-service result (2026-11-01)

GitHub Actions original read:
<https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314633466>.

- All **10 synthetic metadata/safety tests passed**.
- The publisher-documented HTTPS endpoint
  `https://mapproxy.tetraeder.solar/st_luxemburg_25/service?`,
  queried exactly once with `SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0`,
  returned **HTTP 401 Unauthorized** without credentials.
- Therefore **no actual capabilities XML, advertised layer names, WMS
  GetFeatureInfo fields, roof-facet values or per-building records were read**.
  The code distinguishes *passing metadata parser unit tests* from *actual
  denied provider access*. A passing workflow run does NOT mean WMS is open.
- This is consistent with the 2025 vendor PDF remark that WMS access uses
  existing project credentials. No credential guessing, alternate endpoint
  enumeration or unauthorised building enumeration was performed.

**Decision:** Commercial reuse/licence status and the roof-facet WMS remain
`not_reviewed` / `blocked_for_anonymous_access`. The right next
action is an **authorised provider access and reuse request**, not a WMS
scrape. The direct 2025 building SHP has none of `tilt/aspect/flat/area3d`
(from the separate original DBF header test in #951), so its columns
cannot be silently relabelled as roof-slope measurements.

**Alternative independent physical path:** The existing ACT LiDAR2024
MNT (terrain) / MNS (surface) geodata work (PR #950 on main) uses small
original 2024 raster windows, not this restricted WMS. Its original
surface/terrain heights could potentially support roof pitch/height
**only after** identifying actual roof points and validating 3D
definitions against geometry and independent references. The LiDAR
workflow does not itself deliver roof material, exact construction age
or installed photovoltaic equipment.

## Model-data boundary

All rights continue to be `not_reviewed`. The solar cadastre dataset catalogue states **Other (Open)**, and the credentials remark on the WMS can imply additional provider access terms. Do not embed credentials, query identifiable household addresses, attempt to enumerate roofs via a map proxy, download large tiles, import original facets into the insurance Neon database, or claim model admission.

**Next causal step if publicly accessible:** request explicit provider WMS facet layer names and *bounded, rights-cleared* original feature access, study facet-to-building `hid` cardinality with original survey vintage, then compare with ACT2023v2 + EUBUCCO only after source independence and building segmentation checks. **If restricted:** document terms and request access from the original source provider through an authorised channel; use the already catalogued ACT LiDAR MNS/MNT paths for an independent physical roof-height validation instead.
