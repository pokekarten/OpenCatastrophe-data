<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Croatian DGU cadastral Buildings WFS — original GML geometry gate (2026-11-15)

**State:** bounded research preflight, **not** an admitted exposure dataset or verified original GML run. Related source-science issue: [#1458](https://github.com/pokekarten/OpenCatastrophe-data/issues/1458). No downloaded feature data, addresses, coordinates, identifiers or third-party original bytes are committed.

## Verified publisher / catalogue evidence (reviewed 2026-11-15)

- The **DGU-owned NIPP source catalogue**, [dataset 1543](https://registri.nipp.hr/izvori/1709), explicitly describes 2D building polygons from the **Digital Cadastral Map**, advertised INSPIRE `BU:Building`, GML and an open-licence link. The dataset is not a claim that every current building is represented.
- The **paired WFS service**, [NIPP registry ID 1545](https://registri.nipp.hr/izvori/1711), identifies the original endpoint `https://api.uredjenazemlja.hr/services/inspire/bu/wfs`, Croatia-wide geographic scope, cadastral source, a 2023-12-18 listing date and [Croatian Open Licence](https://data.gov.hr/otvorena-dozvola) as its reuse-terms pointer.
- DGU's [official geoportal](https://geoportal.dgu.hr/cms/en/data-and-services/) lists anonymous **Digital cadastral map Buildings WFS** separately from an anonymous **INSPIRE Buildings ATOM** feed under `geoportal.dgu.hr/services/atom/bu-core2d/xml`. The latter is recorded by the [NIPP 1123 dataset](https://registri.nipp.hr/izvori/1138) as sourced from the **Basic Topographic Database**. They are **not** two verified byte-identical representations of the same buildings.
- Registry records advertise an open licence, but the exact operative licence text, commercial automated/bulk access terms, attribution/derivative requirements and individual-artifact redistribution scope were **not independently completed** in this task. Those gates stay blocked. A catalogue date is not a data-vintage date.

## Reviewed public-licence provisions and access caveat

The [official NIPP cadastral WFS entry 1545](https://registri.nipp.hr/izvori/1711) links this particular INSPIRE building service to the [Croatian Open Licence](https://data.gov.hr/otvorena-dozvola); this differs from assuming that every source or restricted layer from the DGU inherits one blanket grant. The [national open-data portal's published Croatian Open Licence explanation](https://www.data.gov.hr/hr/open-license), reviewed **2026-11-15**, explicitly permits commercial and non-commercial reproduction, distribution, adaptation, joining and product integration of covered public-sector information. It conditions reuse on accurate publisher/source attribution (including the latest change date and dataset URI where applicable), identification of changes, and no implication of official provider endorsement. The precise version applicability and publisher-provided attribution wording for a selected original artifact must still be pinned before publication.

The [DGU government CKAN service record](https://catalog.uredjenazemlja.hr/katalogpodataka/inspirewfsserviszaslojzgrada) identifies EPSG:3765, a nationwide *service advertisement* and no public access restrictions in its metadata. This does **not** constitute observed national feature completeness or confirmed unlimited automated scraping. An independent API listing reports a 1,000-feature and 2,000-metre diagonal per-request bound; because that statement has **not** been independently located in authoritative DGU service documentation in this review, it is preserved as an **unverified service-limit lead**, not treated as a provider right or confirmed limit. The reviewed fixed one-feature/849 m request is intentionally below both figures.

**Decision at review time:** general covered information reuse rights have meaningful official evidence, but original artefact scope, API traffic conditions, publication licence evidence and data content/privacy remain unresolved. Do not set `model_input_admitted` or public raw/derived admission true from this review alone.

## Scientific defect closed in the bounded parser

The initial preflight checked polygon closure and signed area but did not reject self-intersecting exteriors with nonzero signed area, duplicate nonadjacent vertices or zero-length edges. Those can produce misleading positive shape results. The revised script rejects such rings using a bounded 2D segment intersection check. It also rejects `gml:interior` until an exact interior-ring/holes profile is independently reviewed, rather than silently approving the exterior as a complete footprint. Synthetic tests cover crossing rings, repeated vertices, zero edges, unsupported interior rings and a valid simple concave exterior. This preflight **still does not** prove provider origin, polygon semantic accuracy, separate-building uniqueness, full topological validity or insured exposure.

## Original topographic ATOM metadata obtained — 2026-11-15

**Original provider response observed:** a direct metadata-only HTTP retrieval of
`https://geoportal.dgu.hr/services/atom/bu-core2d/xml` succeeded through a public
remote HTTP source reader. This is **not** the cadastral `api.uredjenazemlja.hr`
WFS tested elsewhere in this review. The linked official dataset is from the
**Basic Topographic Database** rather than the cadastral Digital Map. Do not
merge, equate, count twice or generalize their source populations.

| Original HTTP/ATOM fact | Recorded value |
| --- | --- |
| Retrieved feed | `https://geoportal.dgu.hr/services/atom/bu-core2d/xml` |
| Original XML response length | **1,958 bytes** |
| Original XML SHA-256 | `ef9b09a02579fd101b8015466f069482ff24ea7781850773a5795b324aabcd8f` |
| MIME type received | `application/xml;charset=UTF-8` |
| Feed and entry `updated` | `2024-03-07T17:05:52.000000+01:00` |
| Entry format/title | INSPIRE **GML 3.2.1**, **ETRS89/LAEA**, compressed ZIP |
| Exact advertised archive URL | `https://geoportal.dgu.hr/services/atom/INSPIRE_Building_(BU-CORE2D).zip` |
| Archive `length` in feed | **285,995,484 bytes (advertised only, unverified)** |
| Archive MIME declared by publisher | `application/x-gmz` (not inferred ZIP header) |

The original XML `rights` text reads **"ograničenje javnog pristupa prema
članku 13 stavku 1 točki (e) INSPIRE Direktive"** (a public-access limitation
referencing Article 13(1)(e) of the INSPIRE Directive). Meanwhile, the
[Croatian national CKAN metadata entry for this topographic Buildings ATOM
resource](https://data.gov.hr/ckan/en/dataset/zgrade-iz-temeljne-topografske-baze-inspire/resource/2b677f84-024e-4773-b2c9-c217e2d2b34b)
describes it as **"Otvorena dozvola (OD)"** and lists a 2026-02-24 catalogue
update. This is a **documented rights/metadata tension**, not proof that a
restricted feed is legally reusable or proof that the catalogue is wrong.
The broad [DGU open-data product page](https://geoportal.dgu.hr/cms/en/data-and-services/)
also lists anonymous access, which is not equivalent to an unconditional
commercial bulk-download and redistribution grant.

**Fail-closed decision:** metadata may be cited; the 286 MB archive was
**not fetched** and its advertised byte length/contents/CRS were **not**
verified from the archive. The archive has no SHA-256 receipt, the legal
rights conflict requires original provider clarification, and scientific
coverage/geometry/model admission remain blocked. Do not infer `approved_raw`,
`approved_derived`, commercial bulk permission, building count or CAT
exposure from this ATOM feed.

**Exact reviewed-release check (added 2026-11-15):** The first
validator version parsed any positive advertised ZIP length and any
timezone-aware `updated`, even when the publisher's release identity changed.
This was a false-positive identity path. The current version now **fails
closed** on departures from the observed `2024-03-07T17:05:52.000000+01:00`
timestamp and 285,995,484 advertised archive bytes. An explicitly requested
`--live` run additionally requires SHA-256 equality with the observed 1,958-byte
feed; offline synthetic tests never claim provider byte provenance, even when
all schema fields appear plausible. This is a *reviewed metadata version pin*,
**not** a SHA of the unacquired 286 MB archive. A genuinely refreshed provider
feed requires independent review and a deliberate profile update.

**Article 13(1)(e) meaning:** The Croatian NIPP
[LimitationsOnPublicAccess code list](https://www.nipp.hr/default.aspx?id=3582)
identifies this particular INSPIRE access-limit code as protection of
**intellectual property rights**, not an assertion about national security or
a claim of confirmed copyright infringement. This increases the need to
reconcile the open-licence catalogue record with the ATOM product's exact
terms before commercial model or public redistribution.

A new bounded validator, `scripts/probe_hr_dgu_topographic_buildings_atom_v0.py`,
inspects a caller-provided XML receipt offline or optionally makes **one
explicit `--live` GET of the exact ATOM feed**. It pins the product identity,
ATOM XML shape, authoritative-restriction notice, timezone-aware update,
exact advertised download link and declared size, and emits only source
metadata/hash and **explicit non-admission** flags. It **never downloads the
ZIP**; the 14 deterministic synthetic tests under
`tests/test_probe_hr_dgu_topographic_buildings_atom_v0.py` challenge missing
restrictions, wrong links, changed size, dates, duplicate entries and unsafe XML.

```bash
python -m unittest tests.test_probe_hr_dgu_topographic_buildings_atom_v0
python scripts/probe_hr_dgu_topographic_buildings_atom_v0.py --live
python scripts/probe_hr_dgu_topographic_buildings_atom_v0.py --offline-file /path/outside/repo/atom.xml
```

The exact observed SHA-256 is evidence for the **2026-11-15 original metadata
response**, not a claim that provider bytes will remain frozen at this URL.
A changed provider feed must be re-reviewed before using the revised release.

## Original service geometry problem

Issue #1458 records a previous **one-feature GeoJSON** Zagreb-area response with `geometry: null`; a separate earlier GML request timed out. Null GeoJSON does not establish absent source GML polygons. Nor does publisher catalogue language establish actual usable polygon bytes in the requested window.

The 2026-11-15 attempted **one-feature original GML request** via remote HTTP fetch timed out after a 20-second limit. The Linux execution environment could not resolve the provider hostname. Accordingly **no live WFS GML polygon was verified this run**, no feature geometry, national count, coverage or original-byte hash is claimed here.

## INSPIRE Core 2D semantic footprint gate (2026-11-15 follow-up)

The European Commission's [INSPIRE Buildings Technical
Guidelines](https://inspire-mif.github.io/technical-guidelines/data/bu/dataspecification_bu.html)
and [approved Buildings2D 4.0 feature
catalogue](https://inspire-mif.github.io/uml-models/approved/fc/)
make a scientific distinction that an exterior-ring geometry test alone
cannot establish: `geometry2D` holds a **BuildingsBase**
`BuildingGeometry2D` object, and its **`referenceGeometry`** and
**`horizontalGeometryReference`** attributes tell consumers which
representation should be used and *what physical building element its XY
coordinates describe*. Roof edges, combined envelopes and building
footprints are not interchangeable CAT exposure footprints.

The earlier synthetic GML tests incorrectly encoded the full nested
representation using the **`bu-core2d`** namespace rather than the
mixed INSPIRE namespace layout, risking a false rejection of schema-correct
GML. The corrected **single-polygon footprint challenge** expects:

```text
wfs:FeatureCollection (1 wfs:member)
  bu-core2d:Building
    bu-core2d:geometry2D
      bu-base:BuildingGeometry2D
        bu-base:geometry / gml:Polygon
        bu-base:referenceGeometry = true
        bu-base:horizontalGeometryReference @xlink:href
          = http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue/footPrint
```

The code now rejects a *valid but unsupported* `gml:Point`,
`gml:Surface` or `gml:MultiSurface`, nil/missing/false or duplicate
reference flags, non-`footPrint` semantics such as `roofEdge` and
`combined`, wrong INSPIRE nested namespaces, and lookalike polygons
that sit outside the one direct `bu-base:geometry` property.
The parser explicitly **does not assert all legitimate INSPIRE encodings
are supported**, only that a passed response is within this tightly
reviewed semantic profile. A provider returning different legal GML must
trigger an independently tested profile rather than an invented
footprint.

The [INSPIRE 4.0 canonical GML
schemas](https://inspire.ec.europa.eu/schemas/bu-core2d/4.0/BuildingsCore2D.xsd)
and [BuildingsBase
schema](https://inspire.ec.europa.eu/schemas/bu-base/4.0/BuildingsBase.xsd)
are the authoritative grammar references; the actual Croatian
`DescribeFeatureType` service response and its schema dependencies
are **not yet byte-verified**, as direct provider requests still timed out.
Consequently this is a stronger independently synthetic **preflight**,
not evidence that the Croatian service actually emits that shape, nor proof
of positional accuracy, legal usage or nationwide completeness.

## Actual footprint/window intersection — envelope false-positive closed

The preceding WFS preflight rejected a footprint only when its **axis-aligned
envelope** lay entirely outside the fixed 600 m × 600 m Zagreb window. An
L-shaped, self-intersection-free building polygon could wrap around the window
corner without touching the window, while the two bounding boxes still
overlap. Such a response incorrectly received
`polygon_envelope_overlaps_fixed_window: true` without spatial evidence
of a real intersection. An envelope is a fast rejection filter, **not** a
topological or spatial proof.

The revised deterministic polygon gate now follows this conservative order
in the fixed EPSG:3765 plane after validating a simple exterior ring:

1. Reject envelopes fully outside the fixed window.
2. Require a real closed-polygon/closed-rectangle intersection using
   polygon vertices in the rectangle, 2D edge crossings or boundary contacts,
   **or** rectangle corners inside the polygon.
3. Return `actual_polygon_intersects_fixed_window: true` only if that
   exact geometric predicate succeeds. No geometry coordinates enter receipts.

Synthetic regression cases cover a disjoint concave L-shaped exterior with
overlapping envelopes (**must fail**), full rectangle containment with no
vertices or crossed edges (**must pass**), a thin crossing strip (**must
pass**) and a **boundary-only touch** (**passes as topological intersection,
not as positive-area exposure**). These deliberately do **not** establish
building ownership, positional accuracy, positive-area overlap, complete
country coverage, calibrated insurance value or permission to reuse data.

The official [Croatian DGU Buildings WFS registry (NIPP service 1545)](https://registri.nipp.hr/izvori/1711)
describes INSPIRE building polygons from the cadastral map, but that catalogue
claim is not a successful raw WFS geometry receipt. This test improves the
honesty of future samples; as of this change, original provider
`GetFeature` GML remains unverified and `model_input_admitted` remains false.

## Executable fail-closed challenge

`scripts/probe_hr_dgu_buildings_gml_window_v0.py` provides an explicit opt-in `--live` request and an `--offline-file` mode. The only allowed live URL is constructed from the exact official WFS endpoint and a fixed 600 m × 600 m **EPSG:3765** Zagreb research window, `bu:Building`, WFS 2.0, `COUNT=1`, `STARTINDEX=0`; no arbitrary URL, feature ID, authenticated service, unbounded paging or full-country acquisition. WFS request diagonal is approximately 849 m. Network has a 15-second timeout, a 512-KiB response ceiling and refuses redirects, compressed transfer, malformed HTTP framing and unsafe XML declarations.

The XML preflight deliberately supports **only one explicitly reference-marked `footPrint` in an inline 2D GML Polygon exterior under `bu-base:BuildingGeometry2D`**: exactly one WFS member, the expected INSPIRE Building namespace, positive nondegenerate simple closed exterior ring (no repeated vertices, self-crossings, zero-length edges or unreviewed interior holes), finite plausible projected XY coordinates, declared EPSG:3765 and a verified geometric intersection with the fixed window (not envelope intersection alone). It rejects missing geometries, wrong classes, unknown geometry encodings, 3D, axis swaps, out-of-window results, multipart payloads and exception reports. Positive output records only source response length/hash and pass/fail claims; no original feature IDs, polygon coordinates, personal data, addresses or building attributes are printed.

Usage (explicit live network only when a reviewer intentionally invokes it):

```bash
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --offline-file /path/outside/repo/original.xml
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --live
python -m unittest tests.test_probe_hr_dgu_buildings_gml_window_v0
```

An offline success is **not proof of provider origin**; only a successful actual `--live` run can mark `live_original_fetch_in_this_run: true`. Even a live positive preflight would confirm just one bounded GML polygon form, not topology/holes, full Croatia coverage, licence clearance, polygon accuracy, insured TIV or CAT-model readiness.

## Bounded original Croatian cadastral WFS shape observed via intermediary (2026-11-17)

A fresh anonymous request to the **official** DGU cadastral
`https://api.uredjenazemlja.hr/services/inspire/bu/wfs` returned an
HTTP 200 GML response **through an external web-fetch intermediary**, using
the already pinned WFS 2.0 `bu:Building`, `COUNT=1`, `STARTINDEX=0`,
EPSG:3765, 600 × 600 m Zagreb window. This is **not** a trusted direct
GitHub/own-Linux `--live` receipt and not an independently verified original
HTTP body SHA-256. Other attempts from the intermediaries yielded timeouts
or HTTP 400 service errors. Our own Linux environment could not resolve
the provider host. Do not promote the fetch to a reliable production API.

The transient, non-retained XML inspection established:

- WFS 2.0 `FeatureCollection` with `numberReturned=1`;
- one `wfs:member` containing the INSPIRE `bu-core2d:Building`;
- `bu-core2d:geometry2D / bu-base:BuildingGeometry2D /
  bu-base:geometry / gml:Polygon / gml:exterior /
  gml:LinearRing / gml:posList`;
- exactly one observed `Polygon` and a 2D closed finite ring within the
  bounded projected window; a `referenceGeometry=true` element was present;
- **native polygon `srsName` exactly
  `http://www.opengis.net/gml/srs/epsg.xml#3765`**, rather than any
  previously accepted URI spellings.

The older OGC HTTP `srsName` form is an explicit EPSG URI syntax, not a
different coordinate reference system (see
[OGC WFS SRS format examples](https://portal.ogc.org/files/8339) and
[GeoServer WFS documentation](https://docs.geoserver.org/main/en/user/services/wfs/webadmin/)).
The newly added code supports **only that exact EPSG:3765 legacy form**,
with a synthetic regression test and negative near-miss cases.
A later bounded 2026-11-17 external-intermediary HTTP 200 GML inspection
also observed the **exact INSPIRE
`bu-base:horizontalGeometryReference` code `combined`**, not
`footPrint`, on the single returned reference-marked BuildingGeometry2D.
This is a **scientifically material negative for the current
single-footprint profile**: even with the corrected EPSG:3765 alias,
`inspect_gml` must reject that response instead of silently treating
`combined` as a cadastral ground footprint. The existing
`test_reject_unreviewed_geometry_horizontal_reference` already
asserts refusal of `combined` and `roofEdge`, so no relaxation or
new profile is warranted. This is an intermediary structural observation,
not an independently hashed direct-provider `--live` receipt; follow-up
must establish whether the publisher offers an explicitly
`footPrint`-labelled geometry product/feature type without assuming that
the current `combined` polygon suffices.

Neither geometry accuracy, a direct live source digest, nationwide
completeness, an admissible alternative footprint profile, nor
specific commercial reuse scope has been independently established.

**Boundary unchanged:** no original XML, source identifiers, coordinates,
building attributes, raw archive or personally identifying records have
been committed to Git. Cadastral WFS and topographic ATOM products remain
separate. The ATOM archive has a conflicting restrictions/open-licence
record; its rights remain blocked. A native Polygon shape alone cannot
admit exposures, insured locations, TIV or model inputs.

## Separate metadata-only semantic audit lane (2026-11-17)

The official [INSPIRE Buildings Technical Guidelines](https://inspire-mif.github.io/technical-guidelines/data/bu/dataspecification_bu.html)
(section 5.4.1.1, Figure 26) give an explicit example where a
`combined` Building geometry merges a part represented by its ground
footprint with another part represented by its lowest above-ground floor.
Thus `combined` is **not equivalent to `footPrint`**; it is not sufficient
for directly extracting insured ground footprints or building-level TIV.
Keep the original strict `inspect_gml` rejection intact.

To make a future **single original-provider WFS response** reproducible even
when it correctly fails the strict footprint gate, the same bounded probe
now has an *opt-in, non-admission* source-label mode:

```bash
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --live --audit-semantics
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --offline-file /path/outside/repo/source.xml --audit-semantics
python -m unittest tests.test_probe_hr_dgu_buildings_gml_window_v0
```

The audit reuses the existing single-feature URL, byte/timeout/redirect
limits, and rejects XML entity declarations, unexpected feature shape,
duplicate properties, non-reference geometries, unsupported CRS, and
unknown reference labels. Its receipt contains **only** the original XML
size and SHA-256, one reviewed label (`footPrint` or `combined`),
and explicit false verdicts for polygon-geometry verification, ground
footprint verification, source-rights clearance and model admission.
No feature IDs, source coordinates, attributes or original bytes are
written. A valid **audit receipt is not a successful footprint check**:
the ordinary `--live`/ `--offline-file` path keeps rejecting
`combined` and must remain the sole stricter semantic profile.

Rights remain **product-specific**: the official
[NIPP 1543 cadastral dataset](https://registri.nipp.hr/izvori/1709)
and its [NIPP 1545 WFS](https://registri.nipp.hr/izvori/1711)
link specifically to the Croatian Open Licence, whereas the separately
sourced *topographic* ATOM archive advertises an INSPIRE 13(1)(e)
access restriction despite other open-licence metadata. No licence
statement for the WFS is inherited by ATOM; operative API constraints,
privacy, exact release terms and explicit model/data admission remain
subject to separate review.

## First direct public GitHub-runner source challenge — 2026-11-17

The dedicated unprivileged, exact-PR GitHub workflow
[`hr-dgu-one-original-gml-semantics.yml`](../../.github/workflows/hr-dgu-one-original-gml-semantics.yml)
ran from commit `b9df3da5`. The 28 synthetic GML tests **passed**
[workflow run 44169526862](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/44169526862).
The **one bounded direct live request reached original XML semantic
validation**, but it was **blocked** at the exact
`BuildingGeometry2D` child-property allowlist:
`unreviewed or duplicated reference geometry properties`.
The runner therefore **did not** emit a valid audit receipt or
an original XML hash. This proves a mismatch between the current
synthetic three-property profile and that particular provider response,
not permission to ignore additional source fields.

A follow-up [run 44169897063](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/44169897063)
passed **30 synthetic tests** and then blocked the single live request
with `original WFS unavailable`. Provider availability or the exact
HTTP status could not be determined from the earlier generic error.
The probe now distinguishes a **sanitized numeric HTTP status** from
network unavailability, without ever logging raw upstream messages or
response body; synthetic HTTP/URL-error tests enforce redaction.

Both original-source jobs are failures by design while evidence is
incomplete. This is not a GitHub private-runner outage. The independent
repository CI for the earlier head had passed, but neither live failure
counts as an original provider footprint, admission, or licence receipt.
Any schema drift must be reviewed property by property before extending
the explicit semantic-audit allowlist.

## INSPIRE-approved extra metadata names; no source admission (2026-11-17)

The [INSPIRE Buildings Technical Guidelines, §5.3.2.2.4
BuildingGeometry2D](https://inspire-mif.github.io/technical-guidelines/data/bu/dataspecification_bu.html)
define three optional **metadata** properties in addition to the
`geometry`, `referenceGeometry` and `horizontalGeometryReference`
fields used by our bounded observation:

- `verticalGeometryReference` — the vertical reference element;
- `horizontalGeometryEstimatedAccuracy` — nominal XY accuracy;
- `verticalGeometryEstimatedAccuracy` — nominal Z accuracy.

These extra properties explained a plausible cause of the earlier
**exactly-three-properties** audit rejection. As of 2026-11-19, a
bounded original-provider response returned through an external HTTP
intermediary **does show** `horizontalGeometryEstimatedAccuracy` by name;
see the byte-pinned receipt below. Its numeric accuracy is **not**
independently validated or admitted. The
`--audit-semantics` mode now allows only those exact INSPIRE base
property names, at most one of each, with no nested child elements.
It checks that the three core properties still occur **exactly once**,
rejects any unrecognised, duplicated or coordinate-bearing additional
element, and records only sorted names of recognized optional fields.
It does **not** parse, display or certify the optional values, accuracy,
original geometry, complete XSD conformance, rights or model fitness.
Tests also verify that `combined` remains rejected by the original
strict `inspect_gml` path, even with optional metadata.

The source workflow previously ran a single original WFS request for
every relevant PR synchronization. After one structurally blocked
original GML response and two intermittent service/network failures,
that causes low-value extra requests. Now automatic PR runs execute
**only the offline synthetic checks**. An original-source request is
exclusively a `workflow_dispatch` step on reviewed `main` once this
workflow has passed review and is present on the default branch.
The current Draft PR **does not** claim such a dispatched live run.
This preserves reproducibility without silently retrying a service
whose automation limits and exact rights remain under review.

## Shared landscape candidate versus original product identity (2026-11-17)

The canonical [Europe national buildings candidate registry](../../landscape/sources-europe-national-building-gaps-20261108.json)
uses `candidate_id=hr.dgu.inspire-buildings-wfs-atom.2026` to
**discover two DGU product/access paths**, not to assert they are the
same geographic dataset. The standalone cadastral WFS probes previously
returned that shared candidate in `source_id` with no separate product
identity; such a receipt could be misread as evidence for topographic
ATOM. To preserve the existing landscape link without creating a
second source-of-truth registry entry, both the strict GML and the
non-admitting semantic audit now report:

- `source_id`: the unchanged, shared canonical **discovery** candidate;
- `source_id_scope=shared_discovery_candidate_not_dataset`;
- `source_product=DGU Digital Cadastral Map INSPIRE Buildings WFS`;
- `source_endpoint=https://api.uredjenazemlja.hr/services/inspire/bu/wfs`.

Deterministic tests compare that endpoint with the distinct ATOM feed
and ZIP URLs, and challenge both receipt modes. A matching candidate
ID never licenses, verifies or admits the separate ATOM product, its
archive, a building footprint, or an insured exposure. No canonical
landscape or admitted source manifest was changed.

## Reproducible bounded intermediary HTTP receipts — 2026-11-19

An independent follow-up using a **zero-retention external HTTP retrieval
intermediary** successfully acquired one response from the existing fixed
**cadastral WFS** `GetFeature` URL (`bu:Building`, WFS 2.0,
`COUNT=1`, `STARTINDEX=0`, `SRSNAME=EPSG:3765`, fixed Zagreb
600 m × 600 m window). This is an independently repeatable intermediary
response, **not** a direct trusted-`main` GitHub runner `--live`
receipt. Both current HTTP retrievals in this research run had the same
3,489-byte response length and showed the same bounded GML structure.
No full provider body, original feature ID, building geometry, coordinates,
addresses or identifiers were committed.

| Receipt | Observed bounded evidence |
| --- | --- |
| Provider request | `https://api.uredjenazemlja.hr/services/inspire/bu/wfs` with exactly the pinned `fixed_url()` WFS parameters |
| Response media type | `application/gml+xml; version=3.2` |
| XML response bytes | **3,489** |
| SHA-256 of intermediary-returned WFS body | `ad301a5f6e9374d16a6b62f64578a34c5d404620a092b4a33610916d23d5fd07` |
| WFS records | `numberReturned=1`; one `wfs:member`, one inline `gml:Polygon` |
| INSPIRE nested profile | `bu-core2d:geometry2D / bu-base:BuildingGeometry2D` |
| Named base properties | `geometry`, `referenceGeometry`, `horizontalGeometryReference`, **`horizontalGeometryEstimatedAccuracy`** |
| `referenceGeometry` | `true` |
| `horizontalGeometryReference` | **`combined`**, not `footPrint` |
| GML polygon-level CRS declaration | `http://www.opengis.net/gml/srs/epsg.xml#3765` |

The additional `horizontalGeometryEstimatedAccuracy` name is already
covered by the *metadata-only* `inspect_semantic_label()` allowlist;
it is **not** permission to interpret or trust its numerical value. The
strict `inspect_gml()` source-science gate **must still reject**
`combined`: it cannot be silently relabelled as an insurer-ready
ground footprint. The presence of one polygon and an official
EPSG:3765 declaration is not independently verified ground-footprint
semantics, positional accuracy, completeness, source rights or CAT
admission.

The separate official **topographic ATOM metadata** feed was re-fetched
without downloading its advertised bulk ZIP: its response remained
**1,958 bytes**, SHA-256
`ef9b09a02579fd101b8015466f069482ff24ea7781850773a5795b324aabcd8f`,
matching the pinned 2026-11-15 feed metadata identity. The ATOM
IP-rights access warning remains separate from the cadastral WFS.

**Official usage evidence (re-checked 2026-11-19):** the
[DGU open-data page](https://dgu.gov.hr/proizvodi-i-usluge/otvoreni-podaci/6596)
lists the cadastral Buildings WFS and topographic ATOM as separate
high-value network products and describes covered data reuse under the
Croatian Open Licence. The [NIPP cadastral WFS service record
1545](https://registri.nipp.hr/izvori/1711) explicitly links **that
cadastral service** to an open licence. This strengthens the product-
specific legal provenance for the WFS but does **not** prove provider
API rate/automation permissions, justify joining the restricted ATOM
archive, certify original footprints, establish insurance use fitness
or authorize bulk source-byte redistribution by inference.

**Conservative decision:** retain Draft / science-source NO-GO;
`model_input_admitted=false`. The exact WFS body was observed through an
external intermediary rather than a trusted main-runner receipt, and
its sole sampled geometry is explicitly **`combined`**, outside the
reviewed `footPrint` acceptance profile. Any expanded science
interpretation needs an independent validated physical ground-footprint
reference and legal/API use review.

## Provider-advertised geometry scope and official INSPIRE `combined` meaning — 2026-11-19

A second, **metadata-only** anonymous request to the fixed **cadastral**
WFS endpoint using `SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities`
was returned through a zero-retention HTTP intermediary. No building
features, identifiers, coordinates, bulk downloads or private tokens were
requested or stored. The **intermediary-delivered XML body** provides a
bounded reproducibility fingerprint, not a trusted direct source-wire
capture or a declaration of feature coverage:

| Service metadata receipt | Observed value |
| --- | --- |
| Endpoint | `https://api.uredjenazemlja.hr/services/inspire/bu/wfs` |
| Media type | `application/xml` |
| XML byte count | **59,448** |
| SHA-256 of intermediary-returned XML | `31ae7c96132b7ce2f14ee5a6639a73252cb975b8543a33df5d12e5c810f9adfe` |
| Advertised feature types in this response | **`bu:Building` only (1)** |
| Advertised `bu:Building` DefaultCRS | `urn:ogc:def:crs:EPSG::3765` |
| Advertised `bu:BuildingPart` | **absent** |

This is a negative **capability-advertisement** observation for the
reviewed service URL and response, not a claim that Croatia does not
maintain building parts or other related data products. No separate
`bu:BuildingPart` GetFeature workflow can be assumed for this exact
WFS just because it is allowed by the INSPIRE conceptual schema.

The authoritative
[INSPIRE Buildings Technical Guidelines, §5.4.1.1, Figure 26](https://inspire-mif.github.io/technical-guidelines/data/bu/dataspecification_bu.html)
explain the **`combined`** horizontal geometry reference using an
example where **BuildingPart A** is represented by its `footPrint`
and **BuildingPart B** by its `lowestFloorAboveGround`; a building
geometry merged from these parts takes the `combined` label.
This is an **illustrative INSPIRE definition**, not a verified statement
that the returned Zagreb building has those parts or exact provenance.
For a CAT exposure, `combined` cannot be equated with a physical
ground `footPrint`, even if the XML encodes a closed `gml:Polygon`
and `referenceGeometry=true`.

One additional synthetic regression test now exercises the **three
actual observed properties together**: legacy native EPSG:3765
polygon URI, `horizontalGeometryReference=combined`, and the optional
`horizontalGeometryEstimatedAccuracy` name. It requires a non-admitting
metadata receipt **without exposing the optional value**, while the
strict footprint validator must still fail closed. No original XML,
building IDs, accuracy values, source coordinates or third-party data
have been added to the repository.

**Scientific decision:** source geometry exists in a bounded response,
but the service does not advertise an independently accessible
`BuildingPart` feature type at this endpoint, and the observed
`combined` reference remains outside the footprint profile. Keep
the original-product CAT-exposure gate **NO-GO**; seek an authoritative
independent footprint representation/lineage rather than relabel the
polygon or silently construct building parts.

## Closed boundary touch versus positive clipped footprint area — 2026-11-19

The existing `footPrint`-only strict preflight checks *topological*
intersection with the 600 m × 600 m research window. A building polygon
can touch that window only at a corner or along an edge: topologically
the polygons intersect, but there is **zero area inside the window**.
Counting that as positive-area exposure would be a scientific error.

The new receipt field `positive_area_overlap_with_fixed_window` is
computed separately by deterministic four-edge polygon/rectangle clipping
and the existing compensated EPSG:3765 projected shoelace area. It
reports `true` only when the clipped area exceeds the **existing**
0.0005 m² numerical tolerance; smaller slivers cannot be certified.
Neither clipped polygons nor coordinates nor measured area are returned.
Edge/corner touches remain topological intersections but yield a false
positive-area flag. Synthetic regression cases cover a crossing strip,
full-window containment, a concave footprint and reversed winding.

This boolean exists only on the **strict `inspect_gml()` footPrint
path**, after complete original-format, reference-semantics and geometry
checks. The observed Croatian WFS `combined` value is **still
rejected** there; the separate non-admitting `inspect_semantic_label()`
makes no area claim. An area overlap alone does not establish building
identity, surveyed ground footprint, actual insured exposure or rights.
The scientific/source NO-GO remains unchanged.

The clipping predicate was challenged offline against nine targeted
synthetic cases and **1,412 independent Shapely-valid synthetic random
polygons**; area-overlap decisions matched the Shapely reference.
These are *offline algorithm checks*, not original-source evidence.

## Next causal evidence

1. Re-run the explicit `--live` command in a network-capable, provider-permitted environment; check original byte count, SHA-256 and the precise GML geometry type. If the original uses GML MultiSurface/Surface rather than Polygon, **retain failure** and add a separately tested exact shape profile; do not weaken the classifier generically.
2. Read the official Croatian Open Licence and DGU service-specific usage conditions in full, capture their dated authoritative evidence, and separate normal dataset reuse rights from automated WFS service restrictions before any bulk retrieval.
3. Independently test multiple small original-provider windows and compare cadastral WFS geometry with **separate** topographic ATOM lineage and EUBUCCO/Overture before any deduplication or exposure admission.
