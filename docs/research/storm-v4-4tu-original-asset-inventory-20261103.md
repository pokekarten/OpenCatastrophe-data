<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original STORM v4 4TU file inventory — publisher-declared bytes only (2026-11-03)

**Source:** `storm.ibtracs.present-climate.v4`, versioned DOI
`10.4121/12706085.v4`, **version 4 published 2022-07-22**.
This is source research, not raw-data acquisition, admission or model validation.

## Evidence at the original publisher's versioned landing page

The 4TU.ResearchData publisher page
[legacy article v4](https://data.4tu.nl/articles/dataset/STORM_IBTrACS_present_climate_synthetic_tropical_cyclone_tracks/12706085/4)
and [versioned dataset URL](https://data.4tu.nl/datasets/01b2ebc7-7903-42ef-b46b-f43b9175dbf4/4)
identify the fixed v4 DOI and show exactly **three** published source assets:

| Provider filename | Provider-declared bytes | Provider-published MD5 |
| --- | ---: | --- |
| `README.txt` | 2,322 | `bcffee2371f9f2dacc16905b91f22202` |
| `Basins of STORM IBTrACS dataset.kml` | 2,612 | `e45ddb50b5d9b7007564b77cfe21a34c` |
| `STORMV4.zip` | 543,251,824 | `d3e5647fa9c01b1ed33c33c0c930eb30` |

The publisher's version-4 page records the July 2022 correction explicitly:
this release fixes both the previously erroneous cyclone categories and duplicate
track identities. **Do not substitute** a previous archive (`STORM_data.zip`,
v2 provider size 545,853,257 bytes) or unversioned/latest DOI, even if a download
succeeds. The named STORM v4 archive is about 543 MB (decimal); do not put it
in public Git.

These names, sizes and MD5s were independently located by a search/fetch of
the published **4TU webpage**, not by a successful GET against
`data.4tu.nl/v2/articles/{uuid}/files`. The canonical 4TU website returned a
temporary maintenance/timeout response during this research. No original file
or 4TU API response bytes were downloaded by this step, and no original
SHA-256 for any asset is yet available.

## Dataset identity and access boundary

The versioned provider permalink contains candidate article UUID
`01b2ebc7-7903-42ef-b46b-f43b9175dbf4`. It is associated with the
STORM publication across versioned provider URLs. It must still be
independently checked against a **real original API response**, where
`uuid`, `doi` and `version=4` agree. Do not turn the legacy numeric
article number `12706085` into a synthetic UUID or use a latest alias.

4TU's [own API lesson](https://4turesearchdata-carpentries.github.io/interoperability-climate-sciences/technical-interoperability.html)
describes the public read-only article `GET /v2/articles/{uuid}` and file
listing `GET /v2/articles/{uuid}/files`. Its separate version API must be
checked for the safest v4-only selector: the documented `/files` route may
follow a mutable latest version. No new network access contract is made
executable in this PR. API service terms, exact request identity, redirect
handling, byte caps and provider response receipts are outstanding.

## Offline parser and deliberately narrow claim

`research_runners/storm_v4_4tu_asset_metadata_preflight_v0.py` accepts two
**separately captured** API JSON responses plus independently supplied
SHA-256s. It requires exact v4 DOI, article UUID, version and title, exactly
three file names, byte sizes, provider-declared MD5 digests and distinct file
UUIDs. It rejects duplicates, hostile download URLs, traversal names,
wrong release IDs, substituted v2/v3 archives, malformed JSON, non-finite
values, and unknown/missing checksums.

Example after a separately reviewed fixed metadata acquisition:

```bash
python research_runners/storm_v4_4tu_asset_metadata_preflight_v0.py \
  --article-json /private/storm-v4-article.json \
  --article-sha256 INDEPENDENT_ORIGINAL_ARTICLE_METADATA_SHA256 \
  --file-list-json /private/storm-v4-files.json \
  --file-list-sha256 INDEPENDENT_ORIGINAL_FILE_LIST_METADATA_SHA256
```

Its **positive** result would only prove the *metadata snapshot* is consistent
with the publisher-declared inventory. The publisher MD5 is not an
independently measured SHA-256 of an original file, and a file list is
not approval to acquire, distribute or use that file as a CAT model input.
The external API payload schema and per-file UUIDs have not yet been observed,
so the offline parser may intentionally fail closed when live values differ
and must be reviewed rather than weakened.

## Scientific role and subsequent gates

The original peer-reviewed [STORM paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7005259/)
describes 13 synthetic track columns, 3-hourly simulation steps,
per-basin-year identities and coordinates in 0–360 degrees longitude.
That description **does not yet prove** that every member of this exact
2022 v4 ZIP retains the earlier documentation's layout or values;
the original v4 README and internal archive structure must be checked.

Before OpenCatastrophe/NextGen consumes any original track bytes:
(1) verify version-specific 4TU API and original file UUIDs; (2) review
commercial acquisition and redistribution for exact selected files;
(3) acquire under a separately approved bounded workflow outside Git,
verifying provider MD5 *and independently measured SHA-256* with original
filenames; (4) inspect README/ZIP structure and basin/year/storm/step/unit
semantics, and validate category/duplicate corrections; (5) develop
separate track-to-wind/surge hazard models and scientific benchmarks.
No provider original asset, model input, insured loss or Neon import is
admitted by this research.

Parent research task: [#1168](https://github.com/pokekarten/OpenCatastrophe-data/issues/1168).
