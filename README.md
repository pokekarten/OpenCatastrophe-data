<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# OpenCatastrophe-data

[![CI](https://github.com/pokekarten/OpenCatastrophe-data/actions/workflows/ci.yml/badge.svg)](https://github.com/pokekarten/OpenCatastrophe-data/actions/workflows/ci.yml)

OpenCatastrophe-data is the open-source data registry, provenance, admission and transformation layer for OpenCatastrophe.

It is **not a raw-data dump**. Its job is to make catastrophe-risk data inputs traceable, reproducible, licence-aware and scientifically inspectable while failing closed on confidential, restricted or unreviewed material.

Humans and AI agents should be able to understand every admitted source and transformation from public repository state; hidden private data stores or chat context are never normative evidence.

## Who this is for

- **AI agents and developers** get explicit repository instructions, machine-readable task and run-evidence contracts, deterministic checks and public PR coordination.
- **Scientists** get source identity, provenance, scientific semantics, limitations, citation metadata and reproducibility rules that distinguish evidence from inference and design.
- **Insurers, reinsurers and brokers** get an auditable public data-contract layer that can support open hazard/risk workflows without turning customer portfolios, claims, treaties, confidential exposure or proprietary vendor data into public fixtures.

The project is pre-alpha. A green repository check proves the recorded technical gates; it is not by itself a claim of scientific sufficiency, regulatory approval, production fitness or permission beyond the exact recorded data scope.

## What belongs here

- dataset manifests and stable source identities;
- licence/terms and admission decisions;
- retrieval/transformation code;
- schemas/validators;
- provenance identities and hashes;
- small independently synthetic or explicitly redistributable fixtures.

Large or restricted source datasets normally stay outside Git.

## Fail-closed data rule

Public downloadability is not permission. An external asset is not admissible for redistribution unless exact provider/product/version/query identity, authoritative rights evidence and the requested repository scope are explicit and compatible.

Rights/admission and scientific fitness are separate gates. Unknown, ambiguous, stale, contradictory, restricted or non-redistributable material remains blocked.

Repository-authored Apache-2.0 licensing never relicenses external datasets.

## Sensitive-data boundary

Never commit personal/customer/claims/insured-portfolio/confidential exposure/valuation data; credentials/tokens/cookies/signed URLs/private endpoints; proprietary vendor event sets/vulnerability/loss outputs; copied material from unrelated private repositories/workspaces; or external raw/derived bytes whose exact committed scope is not explicitly admitted.

De-identifying confidential data does not automatically make it synthetic or safe for public use.

## Current status

**Status: pre-alpha data foundation.**

One source has a metadata-only admission: DWD 10-minute extreme-wind station observations for Germany, version `v24.03`. No DWD measurement bytes or derived external dataset bytes are committed or approved as OpenCatastrophe artifacts.

This keeps the repository data-byte-free while exercising real provenance, rights and scientific-review contracts.

## Quick start

Requirements: Python 3.11+ and Git. Run the definition-of-done command from a Git checkout; source archives alone cannot prove the tracked file set, Git modes or index state used by the hygiene/licensing gates.

```bash
python scripts/check_all.py
```

Focused tools include:

```bash
python scripts/validate_manifest.py path/to/manifest.json
python scripts/manifest_identity.py path/to/manifest.json
python scripts/validate_agent_artifact.py task task.json --expected-repository pokekarten/OpenCatastrophe-data --expected-main-sha <main-sha>
python scripts/validate_agent_artifact.py run run.json --expected-repository pokekarten/OpenCatastrophe-data
```

## Development contract

Development is intended to happen through the public repository. Current public `main`, Issues and Pull Requests are the collaboration source of truth; private chat or archive state must not be required to review an accepted change.

For contributors and coding agents:

1. start with `AGENTS.md` and `ARCHITECTURE.md`;
2. use the most specific Issue Form for non-trivial work and a draft PR as the visible implementation claim for shared surfaces;
3. keep data-rights review and scientific validation separate;
4. use `schemas/agent-task-v1.schema.json` and `schemas/run-evidence-v1.schema.json` when a formal machine-readable task/handoff is useful;
5. run `python scripts/check_all.py` on the exact candidate before handoff.

See `CONTRIBUTING.md` for contribution rules and `SUPPORT.md` before filing support requests. AI tooling is optional and never grants data rights or replaces repository evidence.

## Interoperability direction

The native admission/provenance contract remains authoritative for rights, privacy, exact artifact identity and lineage. Future interoperability may use RDLS/STAC for risk/geospatial metadata discovery, Oasis OED/ORD for insurance exposure/results exchange, and formats such as GeoParquet or CF/Zarr for suitable artifacts. Any implementation must name an exact standard/profile version and preserve lossiness, rights and lineage; no external standard weakens native admission rules.

## Licensing and citation

Repository-authored tooling/docs/schemas/metadata use Apache-2.0 unless explicitly marked otherwise. Third-party data rights remain source-specific and are recorded in manifests/source reviews.

Project citation metadata are in `CITATION.cff`; software/project citation never replaces source-data attribution.
