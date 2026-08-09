---
name: reproducibility-run
description: Run or review a replayable OpenCatastrophe-data validation or transformation with machine-readable evidence.
license: Apache-2.0
---
<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Reproducibility run

Use this workflow when a result, validation, transformation, or interoperability claim needs replayable execution evidence.

1. Re-ground on current public `main`, root `AGENTS.md`, `SCIENTIFIC_METHOD.md`, and `schemas/run-evidence-v1.schema.json`.
2. Pin the repository commit and every material input/config identity. Do not use mutable `latest` labels as durable evidence.
3. Record commands as argv-style values, relevant runtime/environment identity, start/end timestamps, exit status, and deterministic/stochastic mode. For stochastic work, record algorithm, implementation, seed material, stream identity, and draw protocol.
4. Hash and size material outputs. Record validation checks, claims with evidence class/references, limitations, and any exact external-standard/profile version used for interoperability.
5. Never record credentials, signed/private URLs, private endpoints, machine-local paths, confidential/customer/claims/portfolio data, proprietary model assets, or non-admitted external bytes in evidence artifacts.
6. Validate any formal run artifact with `scripts/validate_agent_artifact.py`, run `python scripts/check_all.py`, and report blockers instead of converting them into PASS.

A technical PASS proves only the recorded checks on the recorded identities. It does not itself prove scientific fitness, legal permission, or production suitability.