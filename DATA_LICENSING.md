<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# External data licensing and rights policy

This policy governs external datasets and derived artifacts considered for OpenCatastrophe-data.

## Core principle

A dataset being publicly accessible or downloadable does not by itself grant permission to redistribute, modify, combine, publish derived content, or use it commercially. Rights are evaluated for the exact product/version/access path, intended use, and publication scope.

Repository-authored software licensing, service/API terms, and third-party dataset rights are separate decisions.

## Admission before bytes

Source research starts metadata-first. External data bytes remain outside Git until an exact asset has passed the applicable admission/review. The manifest schema is deliberately fail-closed; absent or ambiguous evidence is not permission.

A candidate issue or research note is not an admission. A provider-level statement does not automatically authorize every product or later release from that provider.

## Independent rights dimensions

A manifest records at least these independent dimensions:

1. **licence/terms status**: `verified`, `unverified`, `conflicting`, or `unknown`;
2. **commercial use**: `allowed`, `restricted`, `prohibited`, or `unknown`;
3. **redistribution**: `allowed`, `restricted`, `prohibited`, or `unknown`;
4. **redistribution scope**: `raw`, `derived_only`, `metadata_only`, or `none`;
5. **personal-data status**: `none`, `contains`, or `unknown`;
6. **confidential/proprietary status**: `none`, `contains`, or `unknown`.

For public asset publication, `unknown` remains blocking. The current project posture also requires commercial use to be explicitly allowed and privacy/confidentiality to be explicitly `none`.

## Source-rights ceiling versus repository review scope

External rights and OpenCatastrophe's internal review scope are deliberately separate.

The source licence/terms set the **maximum** publication scope that may be legally available:

- `metadata_only` permits metadata only;
- `derived_only` permits metadata and derived assets, but not raw source bytes;
- `raw` is the broadest redistribution scope and can support metadata, derived assets, and raw bytes when all other conditions are satisfied;
- `none` permits no public asset under the redistribution decision.

The repository review state can intentionally be narrower:

- `approved_metadata_only` authorizes only metadata publication;
- `approved_derived` authorizes metadata and identified derived assets;
- `approved_raw` authorizes metadata, identified derived assets, and identified raw assets;
- `pending` and `rejected` authorize no public asset.

A public asset is allowed only when **both** the source-rights scope and the repository review scope contain that asset kind, and all other licence/commercial/privacy/artifact-identity gates pass.

Example: a CC-BY source may allow raw redistribution, while OpenCatastrophe has so far reviewed only the source metadata. The manifest may truthfully record source redistribution scope `raw` with repository status `approved_metadata_only`; public metadata can then be admitted while raw bytes remain blocked until an explicit raw review and exact raw-artifact identity exist.

Do not understate known source rights merely to match a narrower current review, and do not broaden repository review merely because the licence theoretically permits more.

## Required authoritative evidence

Before approving an external asset for Git publication, record:

- canonical provider and exact product page;
- exact version/release/query or other stable product identity where available;
- modelling layer and specific intended use;
- access class;
- authoritative licence/terms URL;
- timezone-aware timestamp for when those terms were reviewed;
- terms version/date and content hash where available and meaningful;
- licence name and SPDX expression when a standard SPDX-listed licence genuinely applies;
- attribution requirements;
- commercial-use conditions;
- redistribution conditions and exact scope;
- modification/adaptation/share-alike requirements;
- relevant database-right, privacy, access-control, API/service, or contractual restrictions;
- reviewer, review date, and rationale.

If bespoke terms apply, use a descriptive licence name/reference and do not invent an SPDX identifier. If authoritative terms conflict, record `conflicting` and block publication until resolved.

## Terms can change

Rights review is time-specific. A manifest records when terms were reviewed; publication/release procedures re-check material terms close to release. A previously approved product may require re-review after a provider changes its licence, access channel, API terms, product release, or redistribution conditions.

A terms-content hash is useful evidence when the authoritative page can be captured lawfully and reproducibly, but the hash does not replace interpretation of the actual terms.

## Raw and derived artifacts

Raw and derived artifacts have separate identities. Where acquired/produced, record exact byte size, SHA-256, and a **logical** `external://...` storage reference. Do not place local paths, cloud bucket URLs, signed URLs, private endpoints, or credentials into committed manifests.

Derived artifacts additionally require transformation lineage: code identity and configuration identity. Transformation never creates new rights by itself.

Aggregation, clipping, reprojection, anonymization, resampling, statistical transformation, model inference, or format conversion is not presumed to remove upstream rights or confidentiality obligations.

## Privacy and confidential information

Dataset licensing and privacy/confidentiality are separate gates. A permissive licence does not by itself make personal, confidential, customer, claims, portfolio, or proprietary data appropriate for a public repository.

Removing direct identifiers from confidential data does not automatically make the data synthetic, anonymous, non-personal, or redistributable. If privacy/confidentiality status is uncertain, keep it `unknown` and outside public asset paths.

## Fixtures

A committed fixture must be one of:

- independently generated synthetic data that was not derived from confidential records;
- an exact external raw/derived asset whose manifest explicitly approves that committed scope and whose conditions are satisfied;
- repository-authored metadata that does not reproduce restricted source content.

Small size does not create permission. Sampling a restricted dataset does not automatically create a redistributable fixture.

## Restricted inputs

Restricted inputs may be used only outside Git in an appropriate controlled environment and only when the intended use is permitted. Public code may define an interface for such inputs, but must not include their bytes, credentials, transient access URLs, reconstructed proprietary tables, or confidential metadata.

## No licence laundering

Apache-2.0 for repository-authored tooling does not change, override, sublicense, or sanitize third-party dataset rights. Public-source code, an open SDK, or an open API client likewise does not determine the licence of data accessed through it.

## Engineering and legal review

This policy is an engineering release gate, not legal advice. Automated agents may collect and structure authoritative evidence, but they must not convert ambiguity into permission. Material bespoke, conflicting, or legally uncertain rights remain blocked pending appropriate authoritative or legal clarification.
