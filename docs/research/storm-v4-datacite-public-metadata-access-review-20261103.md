<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independent DataCite public metadata route review — STORM v4 (2026-11-03)

**Scope:** narrow authoritative **metadata documentation** review, not an
executed DOI API request, provider track-file download, license override,
model admission, or a migration to insurance Neon production.

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
   while its v4 correction note distinguishes it from faulty earlier
   versions.

## Current verified engineering boundary

The separate access contract
`access/storm.ibtracs.present-climate.v4.datacite.json` stays
`documented_only` with `probe_contract.mode=none` and
`implementation_decision=document_only`. Its exact fixed URL, byte
bound 256 KiB and independent offline SHA-256 test are appropriate for a
later separately approved bounded T1 run. The profile
`research_runners/storm_v4_datacite_preflight_v0.py` never accesses
the network. DataCite public metadata-service documentation is
independently verified, but provider API **response bytes were not
retrieved or checked** in this review. No live singleton evidence was
produced. A DOI page, dataset-level CC0 label, and public API service
policy **do not** verify 4TU downloadable file identities or the
scientific interpretation of individual simulated years/events.

**Decision:** It is reasonable to merge the **metadata access contract
as documentation-only research code** after exact-head full CI and
review, while keeping the separate provider request, 4TU original-file
retrieval and every CAT/insurance model-admission gate disabled.

## Separate T1 proposal (not executed)

Any future read-only DOI metadata request must pin the exact URL,
declare HTTPS, single request, no credentials, no redirects to unreviewed
hosts, bounded 256 KiB response and timeout, provider response time and
SHA-256, no provider response persisted to Git. Use an operator-owned
contact in the `User-Agent` if routinely automated; do not put private
contacts or secrets in this public repository. Review the actual metadata
fields for DOI, title, publisher, resource type, rights and version and
run the existing offline parser. Treat HTTP 404, 429, 5xx or changed
rights/version as explicit evidence gaps rather than approval.
