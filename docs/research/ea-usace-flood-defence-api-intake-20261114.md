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

## Trusted original GitHub-runner receipts (2026-11-14)

After the bounded canary was merged as [PR #1602](https://github.com/pokekarten/OpenCatastrophe-data/pull/1602)
at `main` squash commit `0f3c02c390e2262d91c5e6d07dd5aa931ca48152`,
the public [original-source workflow run #43642198655](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43642198655)
completed **both independent source matrix jobs successfully**.

The individual job logs contain the following machine-checked receipts. These
are SHA-256 hashes of **transient exact original JSON response entities**,
not ZIP/archive digests, source geometry checksums, or proof of a frozen
producer release:

| Exact source ID | Trusted job ID | Response SHA-256 | Checked schema |
|---|---:|---|---|
| `uk.ea.aims.spatial-flood-defences.2026` | [132592077710](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43642198655/job/132592077710) | `618384c208e0736cd210b9119edab439d5524a6560c78997843715e7371b2dbd` | One OBJECTID-only ArcGIS JSON, no geometry, EPSG:27700 |
| `us.usace.nld.public-floodwalls.2026` | [132592077711](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43642198655/job/132592077711) | `e4ae60379a231c7e4bc4e28f96ab00ffa4e34123b59a4c06fd879b2db63f10f8` | One OBJECTID-only ArcGIS JSON, no geometry, EPSG:4269 |

**What this closes:** the initial missing trusted original direct API read
for two fixed, small and public JSON source capabilities. It is not a
geometric sample, a full dataset, a provenance-complete product/version
archive or license/scientific/model admission. The returned provider bytes
and OID values were neither committed nor written to Neon; the script
printed `data_persisted=false` and `model_admitted=false`.

The earlier intermediary checks and these trusted runner receipts are
**separate observations** with different transport trust boundaries;
do not claim the hashes should match because live provider records and
serialized JSON can change.

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

## Addendum: USACE NLD public Embankments layer 11 (2026-11-15)

The original [NLD ArcGIS FeatureServer layer 11 metadata](https://geospatial.sec.usace.army.mil/dls/rest/services/NLD/Public/FeatureServer/11?f=pjson) documents **Embankments**, distinct from public Floodwalls layer 12 already registered above. The canonical candidate is now `us.usace.nld.public-embankments.2026` in the existing flood-defence source shard. This is a **metadata examination only**, not a trusted original feature or raw-response-byte receipt, geometry dataset, rights grant or model admission.

Source metadata lists `esriGeometryPolyline`, `hasZ=true`, horizontal `EPSG:4269` (NAD83), vertical `NAVD88_height_(ftUS)`, and selected attributes `EMBANK_ID`, `SEGMENT_ID`, `SYSTEM_ID`, `PRIMARY_MATERIAL`, `SURVEY_DATE` and `DATA_SOURCE`. The [official NLD data dictionary](https://levees.sec.usace.army.mil/data-services/dictionary/) explicitly cautions that Z capability does **not** imply elevations are populated and says the current programme has recently moved reference units to *international feet*. The layer metadata still specifies *US survey feet*. This is a material **unit/version conflict**. A future model cannot convert, compare or spatially join elevation/Z until the exact dataset/version and vertical units of selected source records are proven independently. The [USACE public-data description](https://levees.sec.usace.army.mil/about/about-the-data/) notes heterogeneous data freshness and source responsibility.

**Remaining gates:** (1) resolve vertical CRS/unit version from authoritative source, (2) obtain an authorized original fixed-query metadata/one-record receipt with SHA-256 outside Git and verify field types, (3) inspect a bounded geometry for Z-population and quality, (4) reconcile embankment/segment/system identifiers with floodwalls and closure/alignment lines, (5) review dataset/API licensing, commercial automation and redistribution, and (6) test protection hydraulic connectivity independently. Do not equate a line's presence or Z capability with an effective flood barrier. This addendum changes no admission or model-input state.
 
### Source-specific bounded embankment join-field canary (2026-11-15)

PR #1673 extends the existing offline-tested, trusted-main-only runner for a **third fixed NLD source**: Embankments layer 11. Its exact request selects just `OBJECTID,EMBANK_ID` from a single response feature with `returnGeometry=false`, no pagination, no retries, no auth/proxy/redirect and an 8,192-byte cap. A source-specific double-typed `EMBANK_ID` schema distinguishes the layer from the already qualified Floodwalls source. The emitted receipt includes the source ID, CRS, whether this join key is non-null, and a SHA-256 of the transient exact response entity, **never** the record identifiers, geometry, elevations or source bytes. Synthetic negative tests reject floodwall field confusion, extra fields, unexpected geometry, invalid join IDs and malformed payloads.

At the initial code-only PR stage no trusted live embankment read was yet completed. The workflow performs **network reads only on trusted `main`**, never PR branches; the subsequent trusted-main results are captured below. A successful CI/CodeQL check on the draft PR is not equivalent to an original provider response. This remains `not_admitted`; exact vertical-unit resolution, whole-system topology, conditions/rights and hydraulic science remain blocked.

## Three verified direct original-provider receipts (2026-11-15)

Following [merged PR #1673](https://github.com/pokekarten/OpenCatastrophe-data/pull/1673), main commit `662d56f5a4a96d7bc6d83659c08e00c1438de888` triggered [trusted source workflow run #43741910265](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43741910265). The source-specific GitHub job logs were inspected individually. All three jobs succeeded:

| Exact source candidate | Trusted job | SHA-256 of exact transient JSON HTTP response | Validated scope |
|---|---|---|---|
| `uk.ea.aims.spatial-flood-defences.2026` | [132896765587](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43741910265/job/132896765587) | `618384c208e0736cd210b9119edab439d5524a6560c78997843715e7371b2dbd` | EPSG:27700, exactly one OID, no geometry |
| `us.usace.nld.public-floodwalls.2026` | [132896765568](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43741910265/job/132896765568) | `e4ae60379a231c7e4bc4e28f96ab00ffa4e34123b59a4c06fd879b2db63f10f8` | EPSG:4269, exactly one OID, no geometry |
| `us.usace.nld.public-embankments.2026` | [132896765575](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43741910265/job/132896765575) | `44404674d28a78de0dc9bde57919410480447a76a56412a1976d86ce6fbe2d16` | EPSG:4269, one OID and numeric `EMBANK_ID`, `join_id_present=true`, no geometry |

Each independently observed source receipt explicitly reports `data_persisted=false` and `model_admitted=false`. The hashes bind **only tiny ephemeral original JSON responses**, not a frozen dataset release, a ZIP, a levee/polyline feature geometry, protection level, crest/Z elevation or reproducible nationwide snapshot. No source bytes or individual identifiers were placed into public Git or Neon.

The original-runner access gate is now proven for all three identities, including USACE Embankments layer 11. Rights and attribution, precise source vintage, vertical-unit compatibility (US Survey Feet versus International Feet), geospatial topology, flood-hazard protection physics and independent scientific validation **remain unresolved**. Do not translate this technical success into insurance-model admission or insured-loss reduction.

## Original NLD layer 11 vertical-unit/version metadata gate (2026-11-15)

The public [USACE NLD Embankments layer 11](https://geospatial.sec.usace.army.mil/dls/rest/services/NLD/Public/FeatureServer/11?f=pjson) currently advertises the *metadata* fields `heightModelInfo.heightModel=gravity_related_height`, `vertCRS=NAVD88_height_(ftUS)`, `heightUnit=us-foot`, `hasZ=true`, horizontal NAD83 `EPSG:4269`, `isDataVersioned=false`, `isDataArchived=false`, and `archivingInfo.supportsQueryWithHistoricMoment=false`. The separate [USACE NLD data dictionary](https://levees.sec.usace.army.mil/data-services/dictionary/) says the reference units were recently changed to *international feet* and stresses that elevation storage capability does **not** mean Z values are populated. Thus the layer is not an immutable archived event-date/vertical-height source. An individual source snapshot, Z availability and units must be verified independently.

The dedicated `research_runners/probe_nld_embankment_vertical_metadata_v0.py` checks these **conflicting and mutable** service conditions in a fixed-target, metadata-only original GET: no feature query, geometry, elevations, IDs, credentials, redirects, proxies or downloaded bytes retained. It enforces exact source ID/layer/schema, both height-model fields, no historic snapshot support and the negative modelling verdict `unit_conflict_unresolved=true`, `historic_snapshot_supported=false`, `elevation_values_examined=false`, `model_admitted=false`. It emits only a SHA-256 of the ephemeral original metadata response. Any service identity or unit drift fails closed pending a fresh source/rights/science review; a metadata unit difference of approximately 2 ppm must not be silently corrected because the exact actual Z units, crest meaning and validity remain unknown.

Local synthetic-only negative tests cover ArcGIS schema and CRS changes, wrong units, wrong layer, altered historic archive flags, duplicate keys, malformed/oversized bytes, unexpected HTTP origin and CLI no-network default. The existing EA/USACE GitHub workflow executes offline tests on PRs and an additional exact metadata GET **only from trusted `main`** after merge. A green PR CI is not proof that the live metadata job succeeded. This change is research-only and does not broaden rights, source admission, model inputs or source storage.

