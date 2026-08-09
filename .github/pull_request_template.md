<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

## Summary

<!-- What changes, why is it useful, and what is intentionally out of scope? -->

## Public context and coordination

- Related issue: <!-- #123; use N/A only for a truly trivial fix -->
- Base `main` SHA: <!-- 40-character SHA when material to coordination/reproducibility -->
- Shared / single-writer surfaces: <!-- exact paths or none -->
- Durable contracts touched: <!-- schemas/manifests/data policy/CI/agent contract, or none -->

- [ ] I checked current `main` and overlapping public Issues/PRs before making a non-trivial change.
- [ ] This PR is the visible implementation claim for the listed shared/single-writer surfaces; any overlap is explicitly coordinated.
- [ ] This PR can be reviewed from public repository state and cited public evidence; it does not depend on hidden chat/private-repository context.

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

## Validation and handoff

- [ ] `python scripts/check_all.py` passes on the exact PR head.
- [ ] Tests added/updated for durable behavior, or the reason tests are unnecessary is stated below.
- [ ] I inspected the complete diff for unintended files, generated/binary artifacts, rights broadening, and policy/schema changes.
- [ ] If a formal task/run artifact is used, `scripts/validate_agent_artifact.py` accepts it against the intended repository/current-main identity.

Evidence / limitations / blockers / next independent action:
<!-- Keep concise. Link public evidence/issues instead of duplicating live project state. -->
