<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAT-only Neon access-register synchronization audit (2026-11-01)

**Research-only, non-admission.** This is a reproducible *comparison*, not a
database migration, re-import, source acquisition, model input promotion,
rights grant or automatic merge. The canonical GitHub `access/*.json` files
are not equivalent to the broader historic `access_contract` classification
used by some CAT-only Neon research receipts.

## Observed live discrepancy

Independent read-only inspection of the public
`pokekarten/OpenCatastrophe-data` GitHub contents API and CAT-only Neon
`insurance-risk-core / insurance / main` found:

| Evidence | Count |
| --- | ---: |
| `access/*.json` canonical files in GitHub | **51** |
| Exact paths represented in `registry.source_record` | **42** |
| GitHub canonical files with no Neon source-record path | **9** |
| Shared paths with changed Git blob SHA | **1** |
| Research/source receipts *outside* `access/` classified as `access_contract` | **6** |

The nine GitHub-only canonical files are:
- `access/de.berlin.alkis-gebaeude.wfs.json`
- `access/jp.gsi.fgd.building-outline.gml.json`
- `access/jp.mlit.plateau.citygml.3d-city-models.json`
- `access/jp.mlit.plateau.graphql.citygml-shinjuku2024.json`
- `access/jp.nied.jshis.pshm.site-amplification.json`
- `access/noaa.ncei.event-footprint-catalog.portal.json`
- `access/us.calfire.dins.postfire-feature-layer.json`
- `access/us.calfire.frap.historical-fire-perimeters.firep25-1.json`
- `access/us.landfire.lfps.portal.json`

The shared path `access/esa.worldcover.2021.v200.json` has a differing
Git blob SHA. That is evidence of version drift, **not** proof of invalid
source bytes or that the old record may be overwritten.

The six non-`access/` records comprise two Luxembourg research notes and
four research receipts (USGS ComCat, California wildfire, Florida OIR,
Texas TDI). These remain independently useful research observations. They
must not be counted as canonical `access/*.json` contracts, nor should this
audit delete or silently reclassify them.

## Reproduce without credentials in code or Git

1. Pin the exact public GitHub `main` commit under inspection; do not
   compare a moving `main` against an independently changing Neon export
   without recording both observation times. Download the **JSON metadata**
   array (not the provider data bytes) from:
   `https://api.github.com/repos/pokekarten/OpenCatastrophe-data/contents/access?ref=<PINNED_SHA>`
   and save outside the repository as `github-access.json`.
2. Read-only Neon SQL on explicitly selected **main** of the independent
   `insurance-risk-core` project, database `insurance`:

   ```sql
   SELECT source_key, classification, git_path, git_blob_sha
   FROM registry.source_record
   WHERE classification = 'access_contract'
      OR git_path LIKE 'access/%'
   ORDER BY git_path;
   ```

   Export the small returned JSON **array** privately as `neon-access.json`.
   Do not export source `raw_metadata`, customer/claims values or secrets.
3. Run the offline checker:

   ```bash
   python -m scripts.audit_insurance_access_sync_v0 \
     --github-inventory /private/github-access.json \
     --neon-export /private/neon-access.json
   python -m unittest tests/test_audit_insurance_access_sync_v0.py
   ```

The tool requires valid Git blob SHA-1s and unique canonical paths, refuses
empty/malformed/oversized input, and emits only bounded metadata path lists
and counts. Exit `0` means matching **canonical access paths and Git
blob identities only**; exit `2` means manual sync review is needed;
exit `1` is invalid input. Its approval flags are always false, even
when no difference is found. Noncanonical research classifications are
reported separately and do not by themselves falsify path synchronization.

## Correct repair sequence (not executed here)

For each of the nine missing paths, establish its original Git blob,
contract ID, reviewed source terms, status and exact `source_id`. Prefer
metadata-only additive ingestion through the repository's reviewed path;
do not guess `probe_ready` or populate any raw or model-approval flags.
For the ESA WorldCover hash drift, compare both Git revisions and source
provenance before updating *versioned evidence*, not last-writer-wins
records. Keep the six research documents in their own evidence lane,
preserving original rights/approval limits.

The existing `validation-schema-20261031` branch has materially
different source and exposure records. Do **not** force-merge it into Neon
`main` during this synchronization. A clean technical access register
is not an admitted hazard catalogue, insurer TIV or a calibrated CAT model.


## Later pinned read-only audit: 52 GitHub contracts / 42 Neon (2026-11-01)

A separate live comparison against **public GitHub main commit**
`5b6169fa33ceaefc27d63c4e1fbea1124f6951fe` and the CAT-only
`insurance-risk-core / insurance / main` SQL registry found:

| Evidence at this pinned snapshot | Count |
| --- | ---: |
| Canonical `access/*.json` GitHub files | **52** |
| Canonical paths in Neon `registry.source_record` | **42** |
| Exact shared-path Git blob matches | **41** |
| Missing metadata paths in Neon | **10** |
| Shared path with differing Git blob SHA | **1** |
| Separate noncanonical research receipts classed as `access_contract` | **6** |

This **supersedes the 51/9 numbers only for the new pinned snapshot**;
it does not invalidate the earlier historical read-only comparison.
The tenth missing path is
`access/us.calfire.dins.ckan-package-catalogue.json`
(Git blob `84d5394547ca2cd57a2e58400c6b9050f9e96bba`).
The existing nine missing paths listed above remain missing at this snapshot.

### ESA WorldCover: substantive contract revision, not just a changed file hash

Read both exact Git objects for `access/esa.worldcover.2021.v200.json`:

- Neon-pinned historical commit
  `2c9cfeeec62c81609e63e58465f7882622054b7e`,
  blob `830fff1705d6b29d8c88dc423a27c7254608ca50`.
- Current reviewed GitHub file at pinned main commit
  `5b6169fa33ceaefc27d63c4e1fbea1124f6951fe`,
  blob `2884e2f50b495eee3b399f55c08d43cfa100b602`.

The comparison found **16 changed JSON fields**. In particular, source
access status was upgraded from `documented_only` to `probe_ready`;
the operations changed from two documentation-only operations to
six including narrowly bounded original TIFF header, table and block
samples. The fixed N48E009 tile, sample ranges, digests, evidence dates,
rate limits and official rights references were also updated.
The new contract still does **not** authorize CAT-model input, a full
raster import or insured portfolio inference.

**Required resolution:** review the exact source-specific evidence,
allowed network operations and changed terms before recording a
versioned new Neon metadata receipt. This is **not** a harmless hash
refresh: updating the old SQL row in place would destroy the distinction
between its former `documented_only` content and new `probe_ready`
contract. Preserve both immutable commit/blob identities and source
approval flags. No DB writes or source-data imports were performed.
