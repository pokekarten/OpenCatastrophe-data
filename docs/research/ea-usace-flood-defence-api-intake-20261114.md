<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# England AIMS + USACE NLD flood-defence API intake (2026-11-14)

**State: research source candidates only. No raw source redistributions, flood-defence geometry, protection model, inferred defended regions, insured exposures or rights/scientific admissions.**

## Concrete coverage gap and deduplication

The public repository already has a separate coarse **Global Levee Database Inventory**
(`global.gldi.levee-database-inventory.2025`), USACE **National Structure Inventory**
(`usace.nsi.base.2026`), and other flood hazard products. These do not replace
authoritative jurisdiction-specific flood **defence asset geometry and attributes**.
The three new candidate IDs in `landscape/sources-flood-defence-api-20261114.json`
cover the EA spatial layer, a distinct EA linked-maintenance API and the public
USACE NLD floodwall layer. This is scoped to existing issue #1596 and avoids
an independent duplicate global levee inventory.

## Original publisher and terms

| Source | Provider evidence | Reuse interpretation | Original query boundary |
|---|---|---|---|
| EA AIMS Spatial Flood Defences | [2026 national catalogue](https://www.data.gov.uk/dataset/cc76738e-fc17-49f9-a216-977c61858dda/aims-spatial-flood-defences-inc-standardised-attributes) and [provider ArcGIS layer 0](https://environment.data.gov.uk/arcgis/rest/services/EA/SpatialFloodDefencesIncStandardisedAttributes/FeatureServer/0) | Catalogue explicitly identifies Open Government Licence; source-level attribution and exact service snapshot require separate rights review | One OBJECTID only, `returnGeometry=false`, `resultRecordCount=1`, EPSG:27700 |
| EA asset-management linked data | [EA primary developer reference](https://environment.data.gov.uk/asset-management/doc/reference) | API documentation examples declare OGL 3.0; verify link-key and asset-specific scope before use | **Documentation-only**, no live asset value probe |
| USACE NLD Floodwalls | [USACE official services directory](https://nld.sec.usace.army.mil/data-services/services/), [Floodwalls layer 12](https://geospatial.sec.usace.army.mil/dls/rest/services/NLD/Public/FeatureServer/12), [NLD public data-sharing scope](https://nld.sec.usace.army.mil/about/about-the-data/) | USACE says the public NLD data can be downloaded and shared; public layer does **not** entitle users to private detailed records; verify exact product and third-party content | One OBJECTID only, `returnGeometry=false`, `resultRecordCount=1`, EPSG:4269 |

The catalogue and public-service terms are evidence of potential use, not a completed
OpenCatastrophe rights decision. The source geography is not a comprehensive
inventory of all levees in either nation and **not** a licensed structural engineering
model of certified defences.

## Original service observations and trust boundary

On **2026-11-14**, an *external research fetch intermediary* executed exactly two
original publisher URL GETs. **This is not a trusted GitHub-runner execution or
evidence that the provider's raw bytes were archived.**

- EA ArcGIS JSON: `objectIdFieldName=objectid`, `geometryType=esriGeometryPolyline`,
  `spatialReference.wkid=27700`, exactly one response feature containing
  only `attributes.objectid`, and `exceededTransferLimit=true`.
- USACE ArcGIS JSON: `objectIdFieldName=OBJECTID`, `geometryType=esriGeometryPolyline`,
  `spatialReference.wkid=4269`, exactly one response feature containing
  only `attributes.OBJECTID`, and `exceededTransferLimit=true`.

No full feature, coordinate, building location, protected polygon, time-series,
source geometry, source binary, exposure, TIV or sample row was imported into
Neon or the repository. The upstream values themselves are not reproduced.

The repository ships a deliberately opt-in, fail-closed and fixed-target live canary:

```bash
python -m unittest tests.test_probe_aims_nld_flood_defences_v0
# Manual only: two reads, sequentially
python -m research_runners.probe_aims_nld_flood_defences_v0 --live
# Trusted runner: exactly one read from one fixed ID
python -m research_runners.probe_aims_nld_flood_defences_v0 \
  --live --source uk.ea.aims.spatial-flood-defences.2026
```

The [source-specific GitHub workflow](../../.github/workflows/ea-usace-flood-defence-original-receipts.yml)
runs offline-only on Pull Requests; a push to trusted `main` or a manual
dispatch from `main` runs an independent **single-request** matrix job
per original service. It does not read sources from an unreviewed PR ref,
use stored API credentials or upload provider bytes. Actual success must
be checked **per matrix job**, not inferred from the offline job or generic CI.

It makes **at most two GETs per full manual invocation, or exactly one per
source-selected invocation**, only when `--live` is explicitly given, uses no
auth/key/cookie/proxy, refuses redirects, applies a 15-second timeout per GET and
an 8,192-byte body cap. It validates the layer, CRS, one OID-only attribute,
no geometry and no ArcGIS error before printing a SHA-256 of each transient
response body plus `data_persisted=false` and `model_admitted=false`.
It makes no writes, no retry, no pagination and no user-selectable network URL.
A successful trusted run will be a **new** independent result, not an assertion
that the intermediary observation was trusted. The unit tests use synthetic
fixtures only.

## Next causal admission steps

1. Review actual public GitHub-runner output for those **exact two** GETs; compare
   source and schema identities, response digests and transport failures.
2. Independently pin publisher release version/date, full attribution/metadata,
   original geometry CRS and source freshness before any bounded geometry test.
3. For EA, join maintenance metadata only after proven stable asset keys and
   temporal validity. For NLD, compare levee system and floodwall IDs and document
   missing portions and public/private access boundaries.
4. Validate full hazard geometry, hydraulic connectivity, defence performance,
   overtopping/breach assumptions and independent event holdouts. Do not subtract
   flood depth or loss based only on existence of a polyline.
5. Only then request exact asset-scoped licensing and scientific review for a
   defined modelling/redistribution use case. Until then all three registry
   candidates remain `not_admitted`.

This note intentionally does not approve commercial model inputs or archive
original data. Public metadata and small on-demand API tests are not production
exposure or flood-protection datasets.
