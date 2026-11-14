<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL original bytes: trusted GitHub runner (2026-11-04)

## Purpose and authority boundary

Previous merged source work (#1243, #1258, #1268) proved the two original Zenodo metadata identities and shipped offline ZIP member-digest comparison logic, but **the 43 MB original ZIPs could not be fetched from ChatGPT's DNS-restricted Linux environment**. No actual original member hashes were then available.

This change adds the **smallest trusted-main execution lane** for exactly the two publicly downloadable CC BY 4.0-labelled GRWL simplified ZIPs. It is an opt-in scientific verification receipt, not source-data admission, redistribution authorization, production ETL or claim of changed river widths.

Zenodo original record evidence:

| Release | Original record | Fixed ZIP | Bytes | Provider MD5 |
| --- | --- | --- | ---: | --- |
| 2018 | https://zenodo.org/records/1297434 | GRWL_summaryStats_V01.01.zip | 43,194,162 | c37021e144fbff19ae3fc4e701d85d38 |
| 2026 | https://zenodo.org/records/18624542 | GRWL_summaryStats_V01.02.zip | 43,282,861 | cac403c1a59bce7a74432085d3f5bd3a |

Original provider API endpoints are frozen in `research_runners/grwl_trusted_original_byte_proof_v0.py`. It performs only anonymous HTTPS GET with bounded redirect host rules (Zenodo/CERN/AWS), no GitHub credentials in the checkout, a byte cap matching each provider record, streaming source-MD5/SHA-256 checks and deletion of temporary original ZIP bytes after source validation.

## Provider content negotiation finding (2026-11-04)

The second trusted-main run, commit `433330b16cf6694688519d48f4a31f4f373a8026`, workflow [41821762685](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41821762685), successfully reached the live source step but received `original Zenodo HTTP 406; no source proof` on the first download. The prior client advertised `Accept: application/octet-stream, application/zip`; this follow-up switches only that request header to `Accept: */*` while preserving `Accept-Encoding: identity`, two exact source URLs, fixed byte-length/MD5/SHA256 integrity, bounded redirects and fail-closed output. The change avoids assuming the provider's response MIME and is *not* evidence of successful original ZIP download until a reviewed-main run logs the exact source hashes. No redirect weakening, credential acquisition or data admission is authorized.

## CI execution and evidence boundaries

`.github/workflows/grwl-original-summary-byte-receipt.yml` follows the existing `ghcnd-station-prefix.yml` review pattern:

- PR-head: run 19 targeted **synthetic-only** network-control tests and existing offline GRWL structure/member digest suites. **No original network downloads on PR head**.
- On merge to `main`, triggered only by the addition/change of this particular workflow, run a single original-source proof in a public GitHub-hosted Ubuntu job. `workflow_dispatch` on `main` permits explicit future retries only.
- Permitted GitHub token rights: `contents: read`. Checkout credentials are not persisted. No external/source files are uploaded as artifacts or committed.
- Temporary files are named only from frozen provider identities and are automatically cleaned. Stdout contains a machine-readable JSON receipt of original ZIP SHA-256, metadata and **individual uncompressed ZIP-member SHA-256** values, but no geometry, DBF records or raw third-party bytes. An HTTP/network/byte-check failure must fail the job closed with a non-admission error rather than producing a fake result.

Local command for a *trusted* environment with Zenodo DNS access:

```bash
python -m research_runners.grwl_trusted_original_byte_proof_v0 --live
```

Invoke with `python -m` from the repository root: direct path execution does not put the project root on `sys.path` and previously failed the first trusted-main run before contacting Zenodo. Omitting `--live` never contacts a provider.

## Interpretation gate

A successful provider download and ZIP-member comparison can answer whether the uncompressed `.shp`, `.dbf`, `.shx`, `.prj`, `.shp.xml`, etc. **changed at the byte level**. Equal core bytes exclude changes to those original shapefile-core contents, even if compressed ZIP archives differ. A changed `.dbf` or `.shp` triggers a separate scientific per-feature/field-level audit; it does **not** itself prove different widths, altered hydraulic hazard, flood loss, insured replacement values or validated NextGen model readiness.

Additional requirements before any downstream use: review original file-level content, confirm attribution and any upstream linked rights, establish geographic/reference joins to RiverATLAS and independent holdout observations, and explicitly approve use-specific model input. All evidence ceilings remain false by default.

## Evidence pending

At PR creation, **the original hosted run has not yet occurred**. Its first result (success, 429, timeout, redirect-block or file mismatch) must be read from the exact reviewed main workflow run. Do not claim original ZIP acquisition until that result confirms source bytes and their independently computed SHA-256.
