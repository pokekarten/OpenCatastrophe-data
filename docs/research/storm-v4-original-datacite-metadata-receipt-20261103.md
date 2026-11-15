<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# STORM v4 original DataCite DOI metadata: one verified read-only receipt

- Verification date: **2026-11-03** (original public metadata response retrieved, not original STORM tracks).
- Original read-only URL: `https://api.datacite.org/dois/10.4121%2F12706085.v4`
- Provider: **DataCite Public REST API v2**; returned JSON:API singleton record `data.type=dois`.
- Original response bytes: **14,825**.
- Independently calculated SHA-256 of the **captured metadata HTTP response bytes**:
  `90bbb620c7e04632e45b5c86c2998b3b023a55d246b56c2c7f09cc1a66c62f66`.
- Exact DOI and record ID: `10.4121/12706085.v4`, both `data.id` and `data.attributes.doi`.
- Observed title: `STORM IBTrACS present climate synthetic tropical cyclone tracks`.
- Observed publisher: `4TU.Centre for Research Data`.
- DataCite dataset type: `Dataset`; version field: `4`.
- Observed record rights identifier: `cc0-1.0`; publisher-reported metadata last-updated field: `2025-06-01T05:36:28.000Z`.
- DOI resolves to provider version URL: `https://data.4tu.nl/articles/_/12706085/4`.

## What this proves — and what it does not

The exact public metadata response was retrieved and its DOI, version, type, title, publisher and CC0 metadata claim were inspected against the fixed STORM v4 identity. The original response size and original response SHA-256 allow a future offline preflight to verify the **same captured metadata bytes**.

This receipt does **not** prove acquisition, original-byte identity or rights of any STORM track file. No 4TU asset-list or track download was executed, no event-year schema or 10,000-year scientific claim independently validated, and no raw or model input bytes were committed to the repository or written to Neon. A dataset DOI's declared CC0 is not evidence that third-party hazard transforms, insurer TIV, or unrelated datasets carry the same rights.

DataCite explicitly permits anonymous harvesting of its CC0 **DOI metadata** via its Public REST API. Its published unidentified-client limit is 500 requests per five minutes; this repository contract is far stricter: **one exact anonymous singleton DOI metadata GET per user-initiated probe, no retries, no dynamic DOI, no pagination and no asset downloads**. Source-data licensing, 4TU file reuse and any commercial track asset automation remain separate review gates.

## Original supporting documentation

- [DataCite original singleton DOI request](https://support.datacite.org/docs/api-get-doi)
- [DataCite: public CC0 metadata harvesting](https://support.datacite.org/docs/harvesting-datacite-doi-metadata)
- [DataCite: published API rate limits](https://support.datacite.org/docs/rate-limit)
- [STORM v4 institutional record](https://research.vu.nl/en/datasets/storm-ibtracs-present-climate-synthetic-tropical-cyclone-tracks-6/)
- [Canonical STORM v4 source review](../../docs/source-reviews/storm-ibtracs-present-climate-v4.md)

**Gates before original track acquisition:** independently review the 4TU v4 original asset listing, access/licence terms and file/field semantics; freeze each selected provider-native filename, size and independent SHA-256; preserve basin/storm/event/synthetic-year identifiers; separate track catalogues from simulated wind/surge footprints, vulnerability, observed validation and insured losses.
