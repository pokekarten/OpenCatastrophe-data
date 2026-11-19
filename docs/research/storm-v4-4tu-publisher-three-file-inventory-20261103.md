<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# STORM v4 — 4TU original publisher's three-file listing (2026-11-03)

**Status:** public original-publisher *landing-page metadata* inspected; no 4TU API
JSON response, dataset UUID, source-file contents, original-file SHA-256 or CAT
scientific admission claimed.

## Release identity

- Original versioned publisher page:
  [4TU STORM IBTrACS present-climate version 4](https://data.4tu.nl/articles/_/12706085/4).
- Publisher DOI shown on that page: **`10.4121/12706085.v4`**.
- Published: **2022-07-22**, version 4, synthetic tropical cyclone tracks.
- Previously independently verified DataCite *DOI metadata only*:
  [PR #1164](https://github.com/pokekarten/OpenCatastrophe-data/pull/1164)
  and [the precise DataCite metadata receipt](storm-v4-original-datacite-metadata-receipt-20261103.md).
- Provider's v4 release description says older versions suffered category-threshold
  mistakes and duplicate tracks; **do not replace this v4 identity with v1–v3**.

## Exact publicly displayed file list

All lengths and MD5 labels below are **published by 4TU** on the version 4
*landing page*. They were transcribed from the original publisher page, not
measured on downloaded file bodies. A listed MD5 label is **not a verified
cryptographic SHA-256 for the original file**.

| Original publisher filename | Published bytes | Publisher MD5 (not independently byte-verified) | Metadata role |
|---|---:|---|---|
| `README.txt` | 2,322 | `bcffee2371f9f2dacc16905b91f22202` | Publisher documentation; content not inspected |
| `Basins of STORM IBTrACS dataset.kml` | 2,612 | `e45ddb50b5d9b7007564b77cfe21a34c` | Basin geometry metadata; content/geometry not inspected |
| `STORMV4.zip` | 543,251,824 | `d3e5647fa9c01b1ed33c33c0c930eb30` | Main synthetic track archive; ZIP contents not inspected |

**Published three-file total:** 543,256,758 bytes. The publisher's download
page may summarize this total separately; it is **not** a proof of an
uncompressed archive size or a guarantee against archive expansion attacks.
No file URLs are reproduced or executed.

## Example operator-generated transcription

This is **not** a 4TU API response. Create this local JSON explicitly by
transcribing the publisher's *v4* landing-page listing; do not interpret this
example as an independently acquired or re-hashed original ZIP.

```json
{
  "schema_version": "storm-v4-4tu-publisher-listing-transcription-v0",
  "record_doi": "10.4121/12706085.v4",
  "publisher_page": "https://data.4tu.nl/articles/_/12706085/4",
  "version": 4,
  "observation_basis": "manual_transcription_of_provider_landing_listing",
  "files": [
    {
      "name": "README.txt",
      "size_bytes": 2322,
      "publisher_md5": "bcffee2371f9f2dacc16905b91f22202"
    },
    {
      "name": "Basins of STORM IBTrACS dataset.kml",
      "size_bytes": 2612,
      "publisher_md5": "e45ddb50b5d9b7007564b77cfe21a34c"
    },
    {
      "name": "STORMV4.zip",
      "size_bytes": 543251824,
      "publisher_md5": "d3e5647fa9c01b1ed33c33c0c930eb30"
    }
  ]
}
```

Save it outside Git as `storm-v4-publisher-listing.json`. Calculate the SHA-256
of **that local JSON text** with `sha256sum storm-v4-publisher-listing.json`,
then invoke:

```bash
python research_runners/storm_v4_4tu_landing_inventory_preflight_v0.py \
  --snapshot storm-v4-publisher-listing.json \
  --expected-sha256 <the-sha256-printed-by-sha256sum>
```

Do not reuse any previously calculated SHA-256 after reformatting the JSON:
the local **transcription bytes**, rather than publisher original file bytes,
are hashed here. A PASS only compares the normalized metadata to our pinned
publisher listing; it grants no scientific, rights, download or model admission.

## Repeatable, read-only identity test

`research_runners/storm_v4_4tu_landing_inventory_preflight_v0.py` accepts
a local, operator-created, strictly schema-validated normalized transcription
JSON with the exact v4 DOI, page, version, three file names, published sizes
and MD5 labels. It requires an independent SHA-256 of **that transcription
JSON**, not the source ZIP, and rejects file-count drift, v3/v1 substitution,
unknown/path-traversal names, duplicate entries, changed sizes/checksums,
malformed or duplicate-key JSON, and non-finite values.

This test supports **later metadata change detection only**. It does not
authenticate that a caller copied the original provider page faithfully or
establish a trusted 4TU original API/UUID/file-download receipt. The
script's negative output flags deliberately remain false for raw-byte
acquisition, scientific semantics, rights/admission and Neon writes.

## Original 4TU API source binding: still blocked

The [official 4TU API training](https://4turesearchdata-carpentries.github.io/interoperability-climate-sciences/instructor/technical-interoperability.html)
and [Djehuty API documentation](https://djehuty.4tu.nl/api/) describe
anonymous public **metadata endpoints** `GET /v2/articles/{uuid}`,
`GET /v2/articles/{uuid}/files` and a separate version listing.
The landing-page legacy article number `12706085` is **not proof of
the UUID** required for that route. Older historical STORM versions also
used UUID-form DOIs; none is assumed to equal the v4 API dataset UUID.

The 4TU publisher's [policies page](https://community.data.4tu.nl/policies-guidelines/)
links to separate Terms of Use, deposit agreements, restrictions and rights.
No API request to `data.4tu.nl/v2/articles/{uuid}/files` has been
authenticated or asserted in this work. The exact file-list URL must be
assembled *only after* independent provider original UUID/version evidence
and a separate route/terms review, with an explicit fixed-path request
contract. Do not use numeric fallback, latest-version aliases, unknown
redirect targets or alternative file download routes.

## Separate source-data, model and insurance gates

1. Obtain independent original v4 dataset UUID and version-pinned 4TU API
   metadata, with exact original API bytes, retrieval time, digest, access
   response type, status and file entries; compare *three* names, sizes
   and MD5 labels to this static reference.
2. Review intended research/commercial use and original **track-asset**
   licensing; DOI-metadata CC0 alone does not override third-party inputs.
3. Only after separate approval: acquire each exact file *outside Git*
   using constrained, bounded providers, record its independent SHA-256,
   size and archive integrity, and inspect native fields, units, basin,
   event/track identifier and **synthetic year** integrity.
4. Preserve synthetic versus observed storm distinction. A STORM track is
   not yet a grid-level wind/surge footprint or a historical insured loss.
   Native OpenCatastrophe hazard → exposure → vulnerability → policy /
   reinsurance and downstream actuarial modelling must be independently tested and licensed.

Related tracking issue: [#1168](https://github.com/pokekarten/OpenCatastrophe-data/issues/1168).

**Disposition:** publisher landing-page file metadata is **documented**,
original 4TU API UUID and source-file bytes **unverified**, raw CAT
model-input approval and any insurance DB imports **not admitted**.

## Source identity and CI integration boundary (2026-11-03)

This landing-page inventory is **one metadata view of the same STORM v4 publication** that the distinct API-response validator in merged PR #1172 targets. It is not a second independent tropical-cyclone track generator or a second observed-event dataset. A true original-file proof still requires exact 4TU v4 identity and separately authorized original-file bytes plus SHA-256. The failed earlier CI used a now-resolved global Shapely-version conflict (merged fixes #1183 and #1185); it must be replaced by a new **full exact-head** CI result before merger. Do not equate any synthetic offline check to verified API or 543 MB archive acquisition.
