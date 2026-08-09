<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# OpenCatastrophe-data

OpenCatastrophe-data is the public, open-source data foundation for OpenCatastrophe: a registry, provenance, admission and transformation layer for catastrophe-risk data.

It is **not a raw-data dump**. The repository is deliberately metadata-first and fail-closed: public availability does not imply permission to redistribute, and confidential or rights-unclear data must stay out of Git.

## Who this is for

- **AI agents:** explicit repository instructions, machine-checkable gates and public Issues/PRs as the collaboration state.
- **Scientists:** transparent provenance, source identity, scientific assumptions, citation and reproducibility.
- **Insurers, reinsurers and brokers:** auditable data rights and lineage without exposing customer portfolios, claims, treaties or proprietary vendor data.

## Public-data boundary

Never commit credentials, signed/private URLs, private endpoints, personal/customer/claims/portfolio data, confidential exposure or valuation data, proprietary vendor model assets, or third-party dataset bytes without an explicit reviewed redistribution scope.

A source can be useful without being redistributable. Metadata, rights evidence and scientific review should normally come before acquisition.

## Start here

Humans and agents should read `AGENTS.md` and `ARCHITECTURE.md`. Data-source work must also follow `DATA_LICENSING.md`; scientific interpretation must follow `SCIENTIFIC_METHOD.md`.

Run the local definition of done from a Git checkout:

```bash
python scripts/check_all.py
```

The same command runs in GitHub Actions on Python 3.11-3.14. The final hosted check is named `Required` so `main` can be protected by one stable status check.

## Current stage

**Pre-alpha public foundation.** This first public operating layer intentionally contains no external catastrophe dataset bytes. Data manifests, registry contracts and interoperability adapters should be added through normal public PRs after the CI/security operating model is proven.

## Interoperability direction

The native rights/provenance contract remains authoritative. Future adapters may target RDLS/STAC, Oasis OED/ORD, GeoParquet, CF/Zarr or other relevant standards, but an external standard never weakens native rights, privacy, scientific or lineage gates.

## Licence and citation

Repository-authored code, documentation and configuration are Apache-2.0 unless explicitly stated otherwise. Third-party datasets retain their own licences and conditions. See `CITATION.cff` for project citation metadata.
