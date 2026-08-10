<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

## Summary

<!-- What changes, why is it useful, and what is intentionally out of scope? -->

## Primary task and public work claim

- Primary Issue: <!-- Prefer exactly one: `Closes #123` when merge completes it, otherwise `Refs #123`. If Issues are temporarily unavailable, write `Issues unavailable`. -->
- Base `main` SHA: <!-- exact 40-character SHA reviewed before material work -->
- Issue-scoped branch: <!-- prefer `agent/<issue-number>-<slug>` -->
- Shared / single-writer surfaces: <!-- exact paths/contracts or none -->
- Durable contracts touched: <!-- schemas/manifests/data policy/CI/agent contract, or none -->

- [ ] I checked current `main`, open Issues and open Pull Requests immediately before claiming this work, or repository Issues are currently unavailable.
- [ ] No active writer owns the same shared/single-writer surface, or the coordination is explicitly linked below.
- [ ] This draft PR is the visible implementation claim for the listed surfaces.
- [ ] This PR can be reviewed from public repository state and cited public evidence; it does not depend on hidden chat/private-repository context.

Overlapping / coordinated Issue or PR links: <!-- none / #... -->

## Scope contract

Outcome:

Explicit non-goals:
- ...

- [ ] The diff stays within the primary Issue's declared scope, or an atomic exception is explained here.

Atomic exception, if any: <!-- none / explanation -->

## Follow-up handoff

Independent findings are not silently absorbed into this PR. Create a new linked Agent Task Issue for each independent follow-up, identify it as `Follow-up to #<primary-issue>`, record any dependency and the smallest `next_action`, and link it here.

Follow-up Issues: <!-- none / #... -->

If this PR stops before completion, next resumable action on the primary Issue:
<!-- N/A when complete; otherwise one concrete action that does not require private context. -->

## Safety and scope

- [ ] No secrets, private endpoints/URLs, personal/customer/claims/portfolio/confidential data, restricted source bytes, or proprietary model assets were added.
- [ ] No material was copied from unrelated private repositories/workspaces.
- [ ] New repository-authored files have SPDX/REUSE metadata, and direct software dependencies/workflow actions are inventoried where applicable.

### If this PR changes a source, manifest, admission decision, or external data boundary

<!-- Otherwise write N/A. Public downloadability is not permission. -->

- Authoritative provider/product/version and current terms evidence:
- Raw/derived byte state and exact identity/lineage:
- Rights/privacy/admission before -> after:
- Remaining uncertainty/blocker:

### If this PR changes scientific semantics or transformations

<!-- Otherwise write N/A. -->

- Units / CRS / time / quality / missingness / uncertainty affected:
- Evidence and competing interpretation considered:
- Falsifiable validation or reference comparison:

## Validation and durable handoff

Exact PR head SHA: <!-- fill before ready-for-review -->

- [ ] `python scripts/check_all.py` passes on the exact PR head.
- [ ] Tests added/updated for durable behavior, or the reason tests are unnecessary is stated below.
- [ ] I inspected the complete diff for unintended files, generated/binary artifacts, rights broadening, and policy/schema changes.
- [ ] If a formal task/run artifact is used, `scripts/validate_agent_artifact.py` accepts it against the intended repository/current-main identity.
- [ ] Before moving a draft to ready, I re-read the exact current head, full diff, latest PR conversation/review threads and hosted checks.
- [ ] No explicit unresolved `BLOCKER` / `keep draft` finding remains; any such finding is resolved or deliberately superseded in the PR record.

Checks / evidence / limitations / blockers / external-byte state:
<!-- Keep concise. Link public evidence/issues instead of duplicating live project state. -->
