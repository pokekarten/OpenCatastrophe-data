<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Third-party inventory

Reviewed inventory for direct software dependencies, workflow actions and distributed third-party artifacts.

## Runtime/build dependencies

None beyond Python and Git for repository-authored runtime/acquisition-independent tooling. Validation-only and acquisition-only dependencies are isolated below and are not model/runtime dependencies.

## Validation-only YAML dependency

The repository definition-of-done uses the official `PyYAML` package declared in `requirements-validation.txt` as `PyYAML==6.0.3` solely to parse GitHub Actions workflow YAML semantically for immutable action-pin enforcement. This replaces an incomplete lexical regex/denylist scanner that could miss valid YAML spellings of the semantic `uses` key.

Upstream: `yaml/pyyaml`, release `6.0.3` (2025-09-25), MIT. PyPI declares Python >=3.8 and provides current classifiers/wheels covering the repository's Python 3.11–3.14 validation matrix. The validator uses a `SafeLoader` subclass only; arbitrary/custom constructors are not enabled. Repository tests additionally reject duplicate/non-string mapping keys, unsafe merge/custom-tag forms, recursive aliases and non-string `uses` values before the existing reviewed-action SHA allowlist is applied.

The direct PyYAML version is exact but wheel/source hashes are not pinned in this bootstrap requirements file. GitHub Dependency Review remains required on pull requests, CI runs `pip check`, and the dependency has no repository write token or project secrets. Re-evaluate hash-locking or a digest-pinned validation image if publication/release assurance later depends on a frozen validation environment.

## Acquisition-only scientific I/O dependency

The GloFAS v4 upstream-area reader uses the official Unidata `netCDF4` Python package declared in `requirements-glofas-acquisition.txt` as `netCDF4==1.7.4`. This dependency is **not** imported by the normal landscape, manifest or model-evidence tooling. It is required only when an operator intentionally reads the external `uparea_glofas_v4_0.nc` NetCDF4 ancillary.

Upstream: `Unidata/netcdf4-python`, release `1.7.4` (2026-01-05), MIT. The upstream documentation identifies it as the Python interface to the netCDF C library and documents NetCDF4/HDF5 in-memory reads. PyPI declares Python >=3.10 and classifiers through Python 3.14. The repository records the Python package, netCDF-C and HDF5 runtime versions in every GloFAS extraction evidence record instead of pretending that a single Python-package pin freezes the complete native scientific-I/O stack.

The direct `netCDF4` version is exact; its transitive Python/native environment is not fully hash-locked. That is an explicit acquisition-stage limitation. The dedicated hosted CI lane installs the exact direct dependency, runs `pip check`, creates a synthetic NetCDF4 file at runtime and exercises the real reader. A later production/release workflow that treats extraction output as publication-grade evidence should additionally freeze the complete acquisition environment or container image and record its immutable identity.

## CI-only compliance dependency

The hosted licensing gate installs the official REUSE helper declared in `requirements-dev.txt` as `reuse[charset-normalizer]==6.2.0` from PyPI and runs `reuse lint`. It is CI-only: repository runtime/tooling does not import it, the workflow token is read-only, and the job receives no project secrets. The manifest keeps this direct development dependency visible to GitHub's dependency graph and Dependabot rather than hiding it only in workflow shell text.

Upstream: `fsfe/reuse-tool`, release `6.2.0`. Upstream licensing is file-specific and includes GPL-3.0-or-later for original source code, CC-BY-SA-4.0 for documentation, CC0-1.0 for some configuration/data, and Apache-2.0 for some borrowed code. The dependency is used only as a compliance tool; its licences do not apply to repository-authored Apache-2.0 files.

The top-level REUSE version is exact but its Python transitive environment is not hash-locked. This is a known bootstrap tradeoff, not a runtime trust assumption. Prefer the smallest reproducible improvement that does not add a larger mutable CI surface; re-evaluate a fully locked environment or digest-pinned container if the project later depends on CI outputs for publication/release.

## GitHub Actions

`.github/workflows/ci.yml` uses reviewed immutable pins with read-only repository permissions:

- `actions/checkout` `3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`, MIT; re-verified 2026-08-09), with `persist-credentials: false`;
- `actions/setup-python` `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`, MIT; re-verified 2026-08-09);
- `actions/dependency-review-action` `a1d282b36b6f3519aa1f3fc636f609c47dddb294` (`v5.0.0`, MIT; reviewed 2026-08-10), used only on pull requests to reject newly introduced high/critical known-vulnerability dependencies before the stable `Required` gate can pass.

Re-review upstream licence/release identity before changing a pin.

## Vendored source/binaries

None.

## Update rule

Record every new direct software dependency, workflow action or distributed third-party artifact in the same change. External dataset admissions are canonical in `manifests/`, with accepted source-specific evidence in `docs/source-reviews/`; do not duplicate them here. Repository-authored Apache-2.0 licensing never relicenses external data.
