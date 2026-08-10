<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# API and machine-access standard

OpenCatastrophe treats machine access as a first-class property of every data source. The goal is **100% access coverage**, not 100% REST APIs: each source must have either a reviewed API/service contract, a deterministic machine-download route, or an explicit fail-closed research/documentation state.

## Canonical layers

1. `landscape/sources*.json` remains the canonical non-admission discovery registry.
2. `manifests/*.json` remains the canonical admitted-dataset provenance/rights layer.
3. `scripts/build_source_access_inventory.py` deterministically traverses every current landscape source **and every admitted manifest**, links explicit access contracts, and creates a first-pass machine-access/licensing work queue from already recorded access and rights evidence. It never upgrades rights or invents API facts.
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

The generator discovers all `landscape/sources*.json` files and all `manifests/*.json` files. A newly added discovery candidate or admitted dataset therefore enters the access work queue automatically instead of silently missing API/access review. Tests assert that the generated inventory count equals the live repository source count.

## Fail-closed licensing rule

The source landscape intentionally carries `rights_review_status=not_reviewed`. Landscape candidates therefore remain either:

- `license_review_required`; or
- `known_restriction_requires_review` when existing source notes/access hints already signal restrictions such as non-commercial use, provider agreement, paid commercial access, separate licensing, registration/account gates or redistribution concerns.

Admitted manifests may be classified `source_rights_verified` only when their existing manifest has a verified licence and explicitly allows both commercial use and redistribution. That label describes the **dataset/source rights already reviewed in the manifest**; it does not automatically clear separate API/service terms or authorize raw publication.

The access inventory never turns a public URL, API, download button, account or successful HTTP response into a licence approval. A concrete source-access contract may use `dataset_rights_status=verified` only when a source-specific rights review already exists. Unreviewed/conflicting/unknown rights cannot claim that commercial automation or redistribution is allowed. Connectivity, scientific suitability, licence clearance, API/service terms, redistribution permission and repository admission remain separate gates.

## Known licensing and access hotspots

The existing discovery registry already contains several sources where automation must remain fail-closed until source-specific terms are resolved. This is a non-exhaustive human-readable index; the deterministic inventory remains the complete machine work queue.

- `essl.eswd` — the recorded public subset is non-commercial and broader access is agreement-based. A concrete `do_not_automate` contract is checked in.
- `ioc.vliz.slsmf` — the recorded facility policy prohibits commercial use of website data/products and directs commercial users to the underlying data originators; registration/API availability therefore does not clear commercial automation or redistribution. A documentation-only registered-API contract is checked in.
- `iavcei.wovodat.v2` — the registry records original-contributor ownership, redistribution restrictions and free use framed around crisis response, education and research. Commercial/redistribution use needs dedicated review.
- `gem.global-exposure-model` and `gem.global-vulnerability-model` — the registry records open non-commercial/share-alike variants and separate commercial licensing for broader commercial use. Exact release and licence path must be frozen before automation.
- `grdc.global-river-discharge` — the standard portal is recorded as non-commercial research access with redistribution restrictions; keep it separate from GRDC datasets explicitly released for broader reuse.
- `cred.em-dat.public-data` — the registry records free registered non-commercial access and paid commercial access; redistribution and derived-use limits require dedicated review.
- `perils.industry-exposure-database.2025` — this is a high-value insurance benchmark but not an open-data source; exact provider access, commercial and redistribution terms must be reviewed before any connector does more than document the route.

Registration alone is not a licensing problem: Earthdata, Copernicus and similar provider accounts may be perfectly usable when their dataset/API terms allow the intended purpose. The inventory therefore records registration/account gates separately from commercial/redistribution restrictions, and a future credentialed contract must document both.

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

The initial contracts deliberately exercise four different source/access outcomes:

- `access/wsv.pegelonline.rest-v2.dresden.json` — anonymous REST-v2 station metadata for the already reviewed Dresden/Elbe hydrology pilot. The existing strict parser remains the scientific interpreter. Target discharge acquisition is intentionally outside this metadata-only contract.
- `access/dwd.cdc.extreme-wind.http-file.json` — anonymous authoritative HTTP directory/file access for DWD historical extreme-wind observations. This proves that a source can receive a machine-access contract without having a native REST API.
- `access/essl.eswd.public-subset.documented.json` — a documentation-only boundary for ESWD where the existing discovery evidence records non-commercial public use and broader agreement-based access. The correct machine-readable decision is `do_not_automate`, not a scraper.
- `access/ioc.vliz.slsmf.registered-api.documented.json` — the registered IOC/VLIZ API is preserved as a real technical route, while the recorded non-commercial policy keeps automated data use blocked until originator/API terms are explicitly cleared.

These contracts remain bounded by their existing dataset/source review and exact external-byte provenance requirements. A contract can intentionally document a prohibition or unresolved rights boundary; 100% access coverage does not mean 100% automated downloading.

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
