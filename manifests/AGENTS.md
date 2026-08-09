<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Manifest instructions

These instructions apply to files under `manifests/` and extend the root `AGENTS.md`.

- Treat `schemas/dataset-manifest.schema.json`, `scripts/validate_manifest.py`, and the tests as one contract. Do not change manifest semantics in only one of those surfaces.
- Keep source-rights scope separate from OpenCatastrophe review scope. A permissive source licence does not automatically authorize raw or derived publication by this repository.
- Start external-source work metadata-first. Do not add raw or derived artifact identity until exact bytes have been lawfully acquired outside Git, independently identified, and explicitly reviewed for that publication scope.
- Use exact provider/product/version/query identity and current authoritative terms evidence. Unknown, stale, conflicting, or ambiguous rights remain blocking.
- Never place credentials, signed/private URLs, private endpoints, machine-local paths, bucket URLs, or secrets in committed manifests. Storage references are logical `external://` identities, not locations.
- Preserve scientific semantics such as units, CRS, time meaning, quality state, missingness, coverage, and material transformation assumptions.
- Any admission-state change must be reviewable from public evidence in the same PR, with the corresponding durable source review updated when applicable.

Before handoff run the manifest validator, compute the deterministic manifest identity when relevant, and run `python scripts/check_all.py` on the exact candidate.
