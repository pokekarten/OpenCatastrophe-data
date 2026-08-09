<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Schema instructions

These instructions apply to files under `schemas/` and extend the root `AGENTS.md`.

- Treat every public schema as a durable machine contract for humans and multiple AI/tooling providers. Keep contracts closed and explicit; do not add permissive catch-all fields to make a current example pass.
- Keep schema, dependency-free validator behavior, documentation, and negative tests in parity in the same PR. A JSON Schema change without matching executable validation where the repository has a validator is incomplete.
- Preserve exact types. Booleans are not integers; duplicate JSON keys, non-finite values, unsafe paths, mutable `latest` identities, and unsupported extra fields must continue to fail closed where relevant.
- Do not silently reinterpret an existing schema/profile version. A breaking semantic change requires a new version identity and an explicit compatibility/migration decision.
- Rights/admission, scientific evidence, run status, and interoperability claims remain separate concepts. A schema must not collapse those distinctions for convenience.
- Agent-task and run-evidence contracts stay provider-neutral. Do not introduce a mandatory model vendor, MCP host, IDE, or private coordination service.
- Keep examples and tests synthetic or metadata-only unless an exact external artifact has an explicit public admission.

Before handoff run the relevant validator/tests and `python scripts/check_all.py` on the exact candidate.
