<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# API and machine-access standard

OpenCatastrophe treats machine access as a first-class property of every data source. The goal is **100% access coverage**, not 100% REST APIs: each source must have either a reviewed API/service contract, a deterministic machine-download route, or an explicit fail-closed research/documentation state.

## Canonical layers

1. `landscape/sources*.json` remains the canonical non-admission discovery registry.
2. `manifests/*.json` remains the canonical admitted-dataset provenance/rights layer.
3. `scripts/build_source_access_inventory.py` deterministically traverses every current landscape source and creates a first-pass machine-access/licensing work queue from already recorded access hints and notes. It never upgrades rights or invents API facts.
4. `schemas/source-access-v1.schema.json` and `scripts/validate_source_access.py` define the strict contract for a provider interface once its exact access behavior is reviewed.
5. `access/*.json` contains concrete reviewed access contracts. These contracts do not authorize data admission or raw-byte publication.

Generate the current repository-wide inventory:

```bash
python scripts/build_source_access_inventory.py
```

To check in a deterministic snapshot when desired:

```bash
python scripts/build_source_access_inventory.py --write
python scripts/build_source_access_inventory.py --check
```

The generator discovers all `landscape/sources*.json` files. A newly added source therefore enters the access work queue automatically instead of silently missing API/access review.

## Fail-closed licensing rule

The source landscape intentionally carries `rights_review_status=not_reviewed`. The access inventory therefore never turns a public URL, API, download button, account or successful HTTP response into a licence approval.

Every source is initially classified as either:

- `license_review_required`; or
- `known_restriction_requires_review` when existing source notes/access hints already signal restrictions such as non-commercial use, provider agreement, paid commercial access, separate licensing, registration/account gates or redistribution concerns.

A concrete source-access contract may use `dataset_rights_status=verified` only when a source-specific rights review already exists. Unreviewed/conflicting/unknown rights cannot claim that commercial automation or redistribution is allowed. Connectivity, scientific suitability, licence clearance, redistribution permission and repository admission remain separate gates.

## Access classes

The inventory deliberately distinguishes:

- API candidates;
- geospatial services such as STAC/WMS/WFS/WCS/ArcGIS services;
- federated services such as MQTT/HTTP data exchange;
- deterministic bulk/file/object-store/repository access;
- provider-request/agreement access;
- portal/service candidates needing further research; and
- unresolved sources requiring an authoritative API/machine-access search.

Do not label a stable file directory, object store or web-service layer as REST merely to make the interface uniform.

## Concrete contracts

The first two contracts exercise different access models:

- `access/wsv.pegelonline.rest-v2.dresden.json` — anonymous REST-v2 station metadata for the already reviewed Dresden/Elbe hydrology pilot. The existing strict parser remains the scientific interpreter. Target discharge acquisition is intentionally outside this metadata-only contract.
- `access/dwd.cdc.extreme-wind.http-file.json` — anonymous authoritative HTTP directory/file access for DWD historical extreme-wind observations. This proves that a source can receive a machine-access contract without having a native REST API.

Both remain bounded by the existing dataset/source review and by exact external-byte provenance requirements.

## Required contract behavior

A provider-specific contract must define its service root, interface type/version, authentication posture, allowed operations and path templates, bounded parameter policy, expected response media types, scientific semantics, time/byte/retry limits, mutability/versioning, rights/API terms state, safe probe and implementation decision.

Contracts must never contain API keys, passwords, bearer tokens, cookies, refresh tokens, signed private URLs or arbitrary caller-supplied hosts/headers. Credentialed interfaces use symbolic environment/secret names only. A future hosted probe must resolve hosts and paths from trusted default-branch contracts and must not execute arbitrary PR-head network instructions.

## Verification ladder

- **T0 — documented:** authoritative access docs and contract are reviewed; no network required.
- **T1 — anonymous probe:** one bounded metadata/health/catalogue request; response bytes ephemeral by default.
- **T2 — authenticated probe:** only after intentional least-privilege credential provisioning.
- **T3 — bounded sample:** exact request identity, timestamps, byte count, SHA-256, parser result and persistence status are recorded.
- **T4 — operational health:** optional and only for high-value stable interfaces; do not create noisy scheduled checks for every source.

A successful probe is evidence only that the interface responded under the tested contract. It is not evidence that the source is scientifically fit, legally redistributable or admitted.

## Adapter policy

Prefer small provider-shaped adapters. The conceptual surface is:

```text
describe() -> contract metadata
probe() -> bounded evidence receipt
resolve_request(parameters) -> allowlisted request plan
fetch_sample(parameters) -> bounded ephemeral bytes + receipt
validate_response(metadata, bytes_or_stream) -> parser/contract result
```

The caller supplies typed bounded parameters, never an arbitrary URL, shell command, module name, filesystem path or unrestricted headers.

Use `build_adapter_now` only when API access materially improves reproducibility or targeted retrieval and rights/access posture is sufficiently clear. Use `build_later` for valid deterministic access that does not yet justify code. Use `document_only` for unresolved or restricted interfaces. Use `do_not_automate` where provider terms or risk make automation inappropriate.

## GitHub Actions boundary

Issue #165 owns the trusted Actions execution plane. Source-access work must reuse that reviewed plane for any future hosted `api_probe`/acquisition action rather than creating a second privileged network trigger. Anonymous and credentialed probing must remain least-privilege, bounded, secret-redacted and ephemeral-by-default.
