<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Third-party inventory

Reviewed inventory for direct software dependencies, workflow actions and distributed third-party artifacts.

## Runtime/build dependencies

None beyond Python and Git for the current repository-authored validation/tooling.

## CI-only compliance dependency

The hosted licensing gate installs the official REUSE helper declared in `requirements-dev.txt` as `reuse[charset-normalizer]==6.2.0` from PyPI and runs `reuse lint`. It is CI-only: repository runtime/tooling does not import it, the workflow token is read-only, and the job receives no project secrets. The manifest keeps this direct development dependency visible to GitHub's dependency graph and Dependabot rather than hiding it only in workflow shell text.

Upstream: `fsfe/reuse-tool`, release `6.2.0`. Upstream licensing is file-specific and includes GPL-3.0-or-later for original source code, CC-BY-SA-4.0 for documentation, CC0-1.0 for some configuration/data, and Apache-2.0 for some borrowed code. The dependency is used only as a compliance tool; its licences do not apply to repository-authored Apache-2.0 files.

The top-level REUSE version is exact but its Python transitive environment is not hash-locked. This is a known bootstrap tradeoff, not a runtime trust assumption. Prefer the smallest reproducible improvement that does not add a larger mutable CI surface; re-evaluate a fully locked environment or digest-pinned container if the project later depends on CI outputs for publication/release.

## GitHub Actions

`.github/workflows/ci.yml` uses reviewed immutable pins with read-only repository permissions:

- `actions/checkout` `3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`, MIT; re-verified 2026-08-09), with `persist-credentials: false`;
- `actions/setup-python` `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`, MIT; re-verified 2026-08-09).

Re-review upstream licence/release identity before changing a pin.

## Vendored source/binaries

None.

## External source metadata admissions

One metadata-only admission is recorded: DWD `10-minute station observations of extreme wind for Germany`, version `v24.03`; manifest `manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json`; source licence recorded as CC-BY-4.0 from authoritative DWD evidence reviewed 2026-08-08 and re-checked against current DWD Open Data guidance on 2026-08-09; OpenCatastrophe scope `approved_metadata_only`.

No DWD measurement bytes or derived external data are committed/approved as OpenCatastrophe artifacts. The manifest/source-review document is authoritative; this inventory does not broaden scope.

## Update rule

Record every new direct software dependency, workflow action or distributed third-party artifact in the same change. Data assets use the dataset-admission manifest as the primary rights/provenance record; repository-authored Apache-2.0 licensing never relicenses them.
