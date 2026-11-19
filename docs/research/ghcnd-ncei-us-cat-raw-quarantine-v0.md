<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# One verified NOAA US GHCN station → private `cat-raw` (research quarantine)

**State:** executable but **not yet executed against Neon storage**. This is
not a model-input approval, a production DB migration or a source-register
sync. GitHub's source-access contract and the CAT Neon `main` source row are
separate records; do not overwrite historical `documented_only` rows.

## Exact reviewed original

- Provider: NCEI U.S. station `USW00094728.csv.gz`, one fixed HTTPS GET.
- Original GZIP: 1,820,608 bytes, SHA-256
  `d7b482aea03c3d7cbd61cfffc13413c0383f12198b663e2ea203cc0ea03887b1`.
- Decompressed *original* headerless CSV: 16,272,298 bytes, SHA-256
  `95018bf74aea808a70c4495e527e35fcfceaa2eb7cdb4020c532a02b1d1b45c0`.
- Six individually CRC-verified GZIP members; 465,584 original records
  through 2026-10-28; no provider-native OBS_TIME 2400 conversion.
- Original-source workflow receipt:
  https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41504631985

## Private storage upload protocol

The CAT-only Neon main branch has object storage enabled and a **private**
`cat-raw` bucket. Upload object key is content-addressed and fixed:

`research/noaa/ncei/ghcnd/USW00094728/d7b482aea03c3d7cbd61cfffc13413c0383f12198b663e2ea203cc0ea03887b1.csv.gz`

1. Use Neon's **presign storage object (upload)** action for the above bucket/key,
   content type `application/gzip`, on the explicitly selected CAT-only Neon
   branch. Keep the response URL out of logs, Git, PRs, CLI history and
   long-lived configuration. The signed URL expires and must not be published.
2. On a network-capable *authorized* machine, supply that URL only as the
   ephemeral `NEON_CAT_RAW_UPLOAD_URL` environment variable. Execute:
   `python scripts/stage_ghcnd_ncei_us_cat_raw_v0.py --live`.
3. The command checks the signed URL host/path, downloads the exact original
   provider bytes, validates both full SHA-256 hashes, size, CRCs, every
   eight-column station record and the observed date window, and **only then**
   performs a single signed HTTPS PUT. If NCEI has republished the file,
   it **fails closed**, and a new original-source review is required.
4. The receipt names the private bucket/key and reports an upload HTTP
   acknowledgement. It does **not** claim independent stored-byte verification.
   Use a separate signed download from the target bucket and rehash the
   returned 1,820,608 bytes **before** creating a durable Neon
   `registry.artifact` metadata row or granting any raw/model admission.
5. Treat `registry.source_record` historical revisions independently. Existing
   PR #1105 owns the append-only source-contract-revision path and explicitly
   requires independent owner approval before promotion.

### Execution restrictions

- Upload authorization is read **only** from an environment variable, never
  from a CLI argument. The endpoint must be a Neon branchable-storage host
  under the reviewed EU-region service, with the exact `cat-raw` bucket and
  immutable SHA-derived object key. No private project hostname is in Git.
- One fixed NCEI anonymous GET + one signed PUT; no redirects, alternate
  sources, retry loops, dynamic keys, unbounded decompression or GitHub
  Actions secret injection.
- Offline GitHub CI uses synthetic bytes and a fake signed URL; it never
  performs a real upload. The user must execute the upload on an authorized
  network-connected machine using a **fresh** presigned URL.
- WMO/international provider restrictions: **this scope is solely one U.S.
  station**; neither the NOAA distribution contract nor this transfer is a
  blanket grant for non-U.S. stations. Original bytes are stored only in the
  private bucket, never committed into Git.
- A successful upload is a quarantined original-artifact candidate, **not**
  an accepted CAT hazard, exposure, insured portfolio, financial model input,
  or a completed insurer simulation.
