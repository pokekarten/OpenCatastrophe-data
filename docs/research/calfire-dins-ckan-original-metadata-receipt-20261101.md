<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAL FIRE DINS: original public CKAN catalogue response receipt (2026-11-01)

**Evidence class: original HTTP response body, catalogue metadata only.**
No original individual inspection features, site addresses, parcel identifiers,
geometries, personal contact records or actual resource bytes are included
in this repository. This receipt is **not** an admission of source asset data,
a commitment to an automated crawl, or authorisation of the separate
ArcGIS POSTFIRE FeatureServer.

## Exact bounded request and original byte identity

| Item | Observed original provider response |
| --- | --- |
| Endpoint | `https://publish.data.ca.gov/api/3/action/package_show?id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03` |
| Public documentation | <https://data.ca.gov/docs/developer-documentation> |
| Source catalogue dataset | <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data> |
| UTC observation timestamp | `2026-11-01T18:01:22.284Z` (recorded immediately after the request, not an HTTP Date header) |
| Response media type | `application/json;charset=utf-8` |
| HTTP body bytes captured | **16916** |
| SHA-256 of captured **original response body bytes** | `1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8` |
| CKAN action result | `success=true` |
| `result.id` | `1fdaea07-4bcd-4795-aa88-cd72b98e8a03` |
| `result.name` | `cal-fire-damage-inspection-dins-data` |
| `result.license_id` | `cc-by` |
| `result.accessLevel` | `public` |
| `result.isopen` | `true` |
| `result.metadata_modified` | `2026-10-21T20:55:50.264159` |
| Published `resources` | **11** catalogue entries |

The original HTTP response body was obtained through the connected
Context web-scrape interface using its **original bytes** mode, not
an LLM-generated summary or reformatted Markdown. The body SHA-256
was computed directly from the decoded original-byte payload using
a FIPS SHA-256 implementation checked against both standard vectors
for the empty string and `abc`. Neither the source's original HTTP body
nor any returned download URLs have been committed. The only
permanently stored evidence is this small derived receipt and the
independently constructed metadata-only offline checker.

This **single successful historical access** proves public read
connectivity to this CKAN catalogue object on the observation date.
It does not prove an arbitrary future scheduled job will succeed or
authorize a different API endpoint. No original response HTTP status
header was available in this evidence; `success=true` is the
**application-level CKAN JSON field**, not a claim about HTTP code 200.

## Eleven distinct source resource identities, not eleven admitted datasets

| Original CKAN resource UUID | Catalogue format |
| --- | --- |
| `bcb68c2c-fdb6-40f4-9c67-5dfb96efc9f9` | HTML |
| `547d5d5e-1093-415d-acc1-0fa1f1aeec9f` | ArcGIS GeoServices REST API |
| `b8aeb030-140d-43d2-aa29-1a80862e3d62` | CSV |
| `ebd354c6-f5ff-40bf-8164-56fa4e20a533` | ZIP |
| `1e583984-5262-4623-b079-8babf3b0c056` | GeoJSON |
| `3c233d0c-6c92-43af-b650-4fa49176c8b4` | KML |
| `917490df-8758-48ae-aaba-b92e8ab63be9` | ZIP |
| `0931300a-bb71-4f6d-9dfa-eb3bb5acdee3` | TXT |
| `fd2ee9be-8555-43e2-92d7-13a454d0a89c` | XLSX |
| `b449c656-e1f8-4204-9cde-d0ac0b54515f` | GPKG |
| `ed3313e9-06f7-4855-809e-8f484e84d43d` | GDB |

These 11 identifiers belong to **one** public DINS catalogue package.
They are *formats/resources*, not 11 independent observations,
historical releases or independently sampled damage datasets.
Their exact data-file URLs and actual original asset bytes were not
retrieved, downloaded, validated or approved. Catalogue resource
existence does not prove a ready-to-use GIS dataset, spatial validity,
damage/class distribution or complete inspection frame.

## Strict offline schema checker

`scripts/preflight_calfire_dins_ckan_catalogue_v0.py` checks an
independently supplied original package-show response JSON:

```sh
python scripts/preflight_calfire_dins_ckan_catalogue_v0.py --input /trusted/local/dins_ckan_original_response.json
```

The checker requires exact package UUID, slug, `cc-by` catalogue
license label, public/open status, `metadata_modified`, exactly 11
listed resource UUIDs and their advertised formats, and a 64-KiB
maximum. It outputs only selected metadata fields and the SHA-256
of the supplied input, including whether that digest exactly matches
this observed original response. It cannot **authenticate** arbitrary
input bytes on its own: another user could manufacture JSON with the
same identities but a different digest. A matching digest proves
byte-for-byte equivalence with this recorded response, not legal use,
provider trust beyond this source capture, feature-level data quality
or future API entitlement.

`tests/test_preflight_calfire_dins_ckan_catalogue_v0.py`
contains 16 offline synthetic-only positive and adversarial tests;
no third-party sample payloads were embedded as test fixtures.

## Separate scientific, legal and operational gates

The [state developer documentation](https://data.ca.gov/docs/developer-documentation)
states that public CKAN read access is anonymous and programmatically
available. The public [CAL FIRE DINS catalogue](https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data)
reports Creative Commons Attribution and no general public-use restriction.
This supports one anonymous catalogue metadata observation. It does
**not** settle service-specific ArcGIS automated feature-query rules,
commercial bulk extraction, precise address/parcel personal-data
publication, original source-asset licensing boundaries, insurer
portfolio data or vulnerability admission. The CKAN catalogue
access record remains `documented_only` and the separate ArcGIS
source-access contract stays unchanged.

Next scientific step: select one reviewed incident and a separate
verified exposure denominator after rights and privacy review, then
investigate original structure inspection completeness. Do not treat
missing DINS records as undamaged, ordinal damage labels as insured
loss ratios, or catalogue metadata as model-ready source assets.
