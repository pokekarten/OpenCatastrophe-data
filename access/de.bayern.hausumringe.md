<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.bayern.hausumringe.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.bayern.hausumringe.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.bayern.hausumringe

## Source ids

- de.bayern.hausumringe

**Provider:** Bayerische Vermessungsverwaltung / Landesamt für Digitalisierung, Breitband und Vermessung (LDBV)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ldbv.bayern.de/produkte/liegenschaftsinformationen/hausumringe.html>

**Service root:** <https://geodaten.bayern.de>

**Api version:** Official HU-BY Bavarian cadastral 2D Hausumringe SHP district archive 091 Oberbayern; original ZIP 174299765 bytes, source archive year not independently attested

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

- document_exact_oberbayern_zip
- preflight_original_shp_crc_and_member_sha

### Path templates

- /odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip

**Parameter rules:** Document research source and review existing trusted main original-source proof ONLY: no new provider GET/HEAD/Range/whole ZIP, crawling, automatic pagination, retry, caller-selected district/file/path or recurring acquisition under this contract. The separately reviewed existing exact main-only workflow already verified bounded contiguous original source 206 segments for the SHP member; this contract does not duplicate or authorize its replay. Any future version must first review source rate/transport policies and a fresh exact ETag/Last-Modified &amp; full member checksum before source-specific auto-scheduling.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** Original unmodified official 091 Oberbayern HU-BY ZIP 174299765 bytes. Researcher verified only its 'hausumringe.shp' DEFLATE member: exactly 166172236 compressed member bytes and 501212696 decoded native SHP bytes, 2703736 native polygon records, CRC32 55540a66, decoded SHP SHA256 977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c, compressed member SHA256 22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615. Full source ZIP SHA256 NOT verified. Existing trusted provider main workflow 43471636096 validated 20 contiguous original HTTP-206 segments, exact source range, and no provider raw data saved. No original coordinates or polygons persisted in Neon or Git. Existing research samples \#56,\#57,\#61,\#62 and \#94 overlap; do not count as independent new sources.

**Scientific semantics:** BVV HU-BY is German state government 2D cadastral building outline polygons, EPSG:25832, not a federal HU-DE licensed product, ALKIS parcels, individual street address, protected building owner data, policy-level insured building counts or building TIV. Full native SHP member scan verifies exact original geometry representation but not 2020 historical survey truth or the whole zip, as underlying source cadastre vintage lacks independent survey-date proof. Existing GHSL E2020 32x32 geographic study window is a different era; ROI 431083 bbox candidates and 417565 intersecting original polygons are geometric feature counts, not individually insured buildings. Original ROI union 56791644.17 square metres is not insurer exposure or replacement cost. Risk model scientific calibration, independent stock representativeness, temporal alignments, valuation and loss validation are all explicitly blocked.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `8388608`

**Max sample bytes:** `8388608`

**Retry policy:** none

**Rate limit notes:** Official CC BY 4.0 legal permission to use, modify and commercially redistribute the HU-BY open geodata does not itself specify an unlimited source web-server API request cadence, automated full archive mirror rights or request quotas. Prior trusted main workflow used exactly 20 bounded original provider HTTP-206 segments &lt;=8MiB and no retries; no new live calls authorized by this documented_only contract. Review service HTTP transport, acceptable cadence and provider terms separately.

**Mutability notes:** Archive is a maintained cadastral source, not a frozen 2020 shapefile or a verified survey year. Prior HTTP Range proof pinned exact original ZIP object length, member compressed/decoded SHA256 and CRC, HTTP ETag or Last Modified consistency if present, and one GHSL E2020 native window ROI. Whole ZIP SHA256 remains unverified; other SHX/DBF/PRJ members are separately referenced but not a whole ZIP hash. Source regeneration can change bytes/geometry; do not transfer hashes, inferred footprint counts or historical 2020 ground truth across vintages without a new original archive review.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** Official Bayerische Vermessungsverwaltung HU-BY geodata are provided as Open Data under Creative Commons Attribution 4.0 International (CC BY 4.0). Commercial data reuse and modification are permitted with rights holder attribution 'Bayerische Vermessungsverwaltung – www.geodaten.bayern.de', license link, indication of changes, and no implied endorsement. The source-specific research rights ledger permits commercial PRODUCT analysis (not insurance model admission), allows private source proof metadata and research, and labels original-source automated cadence/unreviewed HTTP service policy as conditional or unknown. Do not conflate with Germany-wide BKG HU-DE restrictions, CC BY-ND parcellation or any ALKIS WFS product. No raw building geographies distributed via OpenCatastrophe-data public repository.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html>
- <https://www.geodaten.bayern.de/odd/m/3/html/faq.html>
- <https://www.ldbv.bayern.de/produkte/liegenschaftsinformationen/hausumringe.html>
- <https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096>

**Notes:** Product-scoped source data rights closure for de.bayern.hausumringe / HU-BY (not BKG HU-DE or parcel/WFS). Separate private research Neon sample \#94 was created after successful trusted original-SHP-member Actions run 43471636096 on 2026-11-13 and proves 2703736 full native records and bounded ROI against original GHSL2020 pixels. These geometry facts are research evidence only. This new document-only source contract MUST NOT cause an additional 166MB original-member provider stream: separate source-endpoint API transport/quotas unreviewed, full ZIP hash absent, individual insured buildings/TIV absent, and 2026-era footprints not GHSL E2020 historic survey truth. Seven product-scoped distinct use-case rights entries are in private Neon; no model input approval.
