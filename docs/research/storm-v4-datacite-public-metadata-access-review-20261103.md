<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independent DataCite public metadata route review — STORM v4 (2026-11-03)

**Scope:** authoritative public API documentation plus one independently retrieved
original DOI JSON metadata response on 2026-11-03. This is NOT a provider track
file download, a repository-native runner execution, model admission or Neon write.

## Reviewed primary service documentation

1. [DataCite REST API overview](https://support.datacite.org/docs/rest-api)
   explicitly recommends unauthenticated **Public API** for retrieving
   *Findable* DOI metadata. It excludes Registered and Draft DOI records.
2. [Retrieve a single DOI](https://support.datacite.org/docs/api-get-doi)
   documents exact `GET https://api.datacite.org/dois/{id}` JSON:API
   singleton responses. For this product the frozen **documentation**
   endpoint is `https://api.datacite.org/dois/10.4121/12706085.v4`.
   This is **not** a provider data/track-file endpoint.
3. [DataCite REST API](https://support.datacite.org/docs/api) describes
   public versus authenticated services, REST v2, and recommends an
   identifying `User-Agent` with an operator-controlled contact address
   for routine API integrations. No contact address is invented or stored.
4. [DataCite API rate limits](https://support.datacite.org/docs/rate-limit)
   documents up to 500 requests per five minutes per IP for unidentified
   requests, 1,000 identified and 3,000 authenticated (current published
   policy). This is an upper bound, **not** an appropriate sampling rate.
   A future T1 proof should need **one** GET, no bulk harvesting, no
   forced retries, no guessed credential or automatic redirection.
5. [VU Amsterdam original STORM v4 dataset entry](https://research.vu.nl/en/datasets/storm-ibtracs-present-climate-synthetic-tropical-cyclone-tracks-6/)
   directly identifies DOI `10.4121/12706085.v4` and publisher
   4TU.Centre for Research Data. It labels the v4 dataset **CC0-1.0**,
   and distinguishes this release from earlier STORM variants.

## Current verified engineering boundary

The canonical access contract `access/storm.ibtracs.present-climate.v4.datacite.json`
is now `probe_ready` for exactly one manual, opt-in anonymous `metadata_get` operation.
The repository-native runner `research_runners/storm_v4_datacite_probe_v0.py`
requires the explicit `--probe-once` flag and rejects default execution.
It fixes the original URL and DOI, refuses redirects and unreviewed media types,
uses a 256-KiB cap and 20-second timeout, forbids retries and emits a metadata-only receipt.
There is no automatic, recurring or broad harvesting.

An independent external single-DOI API observation has now been completed:
`https://api.datacite.org/dois/10.4121%2F12706085.v4`.
Original JSON response: **14,825 bytes**; SHA-256 of original captured response bytes:
`90bbb620c7e04632e45b5c86c2998b3b023a55d246b56c2c7f09cc1a66c62f66`.
The response reports exact v4 DOI (both `data.id` and `attributes.doi`),
`types.resourceTypeGeneral=Dataset`, `version=4`, STORM title, publisher
`4TU.Centre for Research Data`, and a `rightsIdentifier=cc0-1.0` claim.

Original [DataCite Data File Use Policy](https://support.datacite.org/docs/datacite-data-file-use-policy)
allows open CC0 reuse of its deposited DOI metadata, while expressly excluding
linked datasets and resources from that CC0 waiver. The record verifies neither
any 4TU track-file name/size/hash nor 10,000-year event semantics, wind footprints,
vulnerabilities, insurer TIV, or model admission.

The exact observation is recorded separately in
`docs/research/storm-v4-original-datacite-metadata-receipt-20261103.md`.
The **repository-native one-shot runner itself has not been executed against
the public API**; the external source observation must not be presented as such.

**Decision:** keep the draft until the latest-head CI and independent source review pass. The T1 receipt is metadata-only; no original STORM tracks or model inputs are admitted.

## Next source-asset gate (still blocked)

Before obtaining STORM v4 track files, independently review the 4TU version-specific
asset listing and automation/redistribution terms. Freeze each selected source-native
filename, file size, SHA-256 and native schema; preserve event, basin, storm and
synthetic-year identities. Track catalogues must remain distinct from wind/surge
hazard footprints, exposure, vulnerability and insured loss.

The DataCite metadata probe cannot approve or download these track assets.
