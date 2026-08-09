<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Security and sensitive-data reporting

This repository is public. Treat Git history, issues, PRs, Actions logs and release artifacts as publicly visible.

## Supported state

OpenCatastrophe-data is pre-alpha and has no stable release line yet.

| State | Security support |
| --- | --- |
| current `main` | yes |
| tagged releases | none yet |
| older commits | no; historical snapshots only |

Security fixes are applied to current `main`.

For vulnerabilities or accidental sensitive/restricted-data exposure, use GitHub private vulnerability reporting when available. Do not test a suspected issue with real confidential data and do not disclose sensitive details in a public issue.

## Never publish

- credentials/tokens/cookies/signing material;
- signed/private URLs or private endpoints;
- personal/customer/claims/insured-portfolio/confidential exposure/valuation data;
- proprietary vendor model assets or restricted dataset bytes;
- copied material whose rights/provenance are not independently reviewable.

If a credential or sensitive asset is exposed, revoke/contain it first. A later deletion does not erase public exposure.

## Reporting fallback

If GitHub private vulnerability reporting is temporarily unavailable, do not publish sensitive details in a public issue. Use the repository Security surface and maintainer contact mechanisms exposed by GitHub rather than posting secrets or restricted data.

## Data rights are separate

A security review does not grant dataset redistribution rights, and a licence/admission review does not prove scientific fitness. Follow `DATA_LICENSING.md` and `SCIENTIFIC_METHOD.md` separately.

## Workflow/dependency security

Keep Actions permissions minimal, use reviewed immutable action pins, and record direct software/workflow dependencies in `THIRD_PARTY.md`.
