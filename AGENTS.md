<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->
# Agent operating contract

OpenCatastrophe-data is designed to be agent-readable without hidden chat or private-repository context.

Before editing, read `README.md`, `ARCHITECTURE.md` and task-specific policy. Work from current public `main`; public repository state is authoritative for collaboration. Issues and PRs are live coordination state, not private transcripts.

Non-negotiable rules:
- never commit secrets, private endpoints, customer/claims/portfolio/confidential data, proprietary vendor assets or unapproved external dataset bytes;
- public downloadability is not permission;
- unknown or contradictory rights remain blocking;
- rights/admission and scientific fitness are separate gates;
- never weaken validation or broaden data scope merely to make a task pass;
- use deterministic, synthetic, offline tests by default.

For external sources, record exact provider/product/version and authoritative terms evidence. For scientific changes, preserve units, CRS, time semantics, quality, missingness, uncertainty and transformation assumptions.

Before handoff run `python scripts/check_all.py`, inspect the complete diff, and report evidence, checks, assumptions and blockers. If the task requires non-public context to understand or review, it is not agent-ready.
