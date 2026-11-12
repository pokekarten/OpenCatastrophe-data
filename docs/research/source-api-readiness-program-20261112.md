<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# All-source API and data-contract readiness program — 2026-11-12

## Scope and truthful status

The canonical landscape and accepted manifest registry, not a scraped URL list,
defines the completeness boundary. This program audits **every** record on the
checked-out commit, validates the existing access-contract inventory and
assigns a machine-readable next gate. It does **not** claim that every entry has
an API, a reusable data licence, a working asset download or CAT-model fitness.

At the initial review: 692 non-admitted discovery candidates, 15 accepted
manifests, 707 total records, 68 reviewed source-access contracts, of which 17 have exact,
separately reviewed public probe programs. The independent insurance research
database held 29 narrowly scoped samples from 20 source identities and 14
product-scoped commercial-rights decisions. Those database counts are an
external observation on 2026-11-12, **not** a continually synchronized Git
registry, data admission or assertion that any provider bytes reside in Git.

## Reproducible audit of the whole register

From a Git checkout with repository validation requirements installed:

~~~sh
python -m unittest tests.test_source_api_readiness_v0 -v
python -m scripts.source_api_readiness_v0 \
  --json /tmp/source-api-readiness.json \
  --markdown /tmp/source-api-readiness.md
~~~

The JSON has one row for **each canonical registry entry**, including its
source ID, registry path, associated access contracts and statuses, recorded
rights posture, explicit missing gate and next action. The report contains a
canonical source-inventory digest. No external network request occurs in audit
mode. The report is generated deterministically from reviewed, versioned
repository state; generated output is not another independently edited truth.

The GitHub Action
[All-source rights and API readiness gate](../../.github/workflows/source-api-readiness.yml)
runs this exhaustive **offline** audit on relevant PRs, on its weekly schedule
and by manual dispatch, placing the full per-record table into the job summary.
It writes JSON into temporary runner storage, **not** an unapproved permanent
raw-data or externally accessible artifact. Re-run against an exact commit to
reproduce the source contract classification.

## Actual bounded live testing

Run the workflow manually from the GitHub Actions tab and choose
the probe_mode option reviewed_17. This is the **only** trigger that performs
live network checks in this workflow. A single read-only runner executes the
seventeen existing provider-specific scripts **sequentially** rather than creating
a matrix of seventeen runner jobs. It does not accept a free-form URL, credential,
source ID, search area or download path.

Before any network request, every allowlisted contract must remain
probe_ready, anonymous, credential-free, with verified dataset rights,
reviewed API terms and permitted commercial automation. A contract change
invalidates the full live preflight until reviewed. Every provider-specific
script enforces its own original URL, operation, response bounds and format.
Logs contain only source access IDs, PASS/BLOCKED and strictly typed
64-hex SHA-256 receipts of the **bounded original response** (two object
receipts where an exact metadata contract permits two requests). Any program without
this digest, or with nonzero exit, is BLOCKED. Raw provider responses and
provider-specific untrusted error text are not copied into job summaries.

The eleven fixed probe contracts cover geoBoundaries DEU ADM1, GFZ Kp,
NOAA SWPC, PEGELONLINE Dresden, EMSC, DWD historical source directory,
ESA WorldCover GeoTIFF header, Global Dam Watch Figshare metadata, NOAA
CO-OPS one-day observations, STORM/DataCite metadata and USGS 3DEP
catalogue metadata, plus four original NOAA GHCN-Daily contracts: NCEI
single-station compressed CSV, NODD single-station complete CSV, a fixed 64-KiB
CSV prefix and two tiny version/country metadata objects, plus one
Berlin ALKIS building WFS 2.0.0 GetCapabilities XML metadata request. The
Berlin test reads no building geometry, addresses, owner attributes, or other
features. The seventeenth contract adds one MeteoSwiss hail-climatology
STAC Collection metadata GET; it does not retrieve or follow NetCDF assets,
STAC items, monthly data or return-period surfaces. They are limited **capability** probes, not complete
downloads, all-regions proofs or model-input approvals. Some exact original
provider terms explicitly limit automation cadence; therefore the weekly
audit **never** schedules live provider requests.

## What is missing and how to add the next source

1. **Missing exact access contract:** select the correct provider product,
   version, native access type (REST/FDSN/OGC/STAC/WFS/WMS/file/SDK), original
   API documentation and applicable service terms. Do not treat every source
   as a REST API.
2. **Unreviewed or conflicting rights:** record dataset and API/service terms
   separately, including the exact product/version, third-party content,
   commercial use, automation, attribution, publication and data retention.
   Conflicts, account gates and requests for permission remain blocked.
3. **Concrete interface but no approved probe:** add an exact reviewed
   source-access contract, immutable probe URL/operation, strict schema and
   negative/offline tests; keep sample scope, redirects, response bytes,
   timeouts, quotas and failure policy bounded. Only then explicitly expand
   the fixed-runner allowlist and this program's tests.
4. **API reachable, sample missing:** collect a *small*, rights-cleared,
   original-provider sample **outside public Git** with request identity,
   SHA-256 of received bytes, response content type, source version, retrieval
   time, unit/CRS/time semantics and licence evidence. Do not equate a
   response SHA with a processed JSONB sample SHA.
5. **Provider sample available, model admission absent:** independently
   validate geometry, numeric semantics, data vintage, uncertainty,
   completeness, resolution, independent holdout suitability and current
   model-consumer role. Record scientific and rights admission separately.

Git must retain canonical source descriptors, contracts, executable
validation and public metadata-only receipts. External payloads, private
exposure, insurer portfolios, vendor files and secrets remain in their
authorized storage systems. A passing green GitHub Action is **never**
a blanket licence to redistribute or consume source data in CAT models.
