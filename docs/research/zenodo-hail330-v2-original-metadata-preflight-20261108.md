<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Zenodo 330-year European hail v2: source preflight, pilot and scientific boundary

Date: 2026-11-08. **Research only / NOT_ADMITTED**.

## What the publisher actually provides

- Original Zenodo release **v2**, published 2025-12-08: https://doi.org/10.5281/zenodo.17860440
- Method: Schmid, Gebhart, Bresch, *Climate Services* 41 (2026), 100630, https://doi.org/10.1016/j.cliser.2025.100630
- Derived from 11-year (2011-2021) 2.2 km COSMO/HAILCAST simulations, spatially resampled into a **330-year event set** separately for REF and +3°C PGW. Same parent simulations as https://doi.org/10.3929/ethz-b-000701925 and https://doi.org/10.3929/ethz-b-000745185.
- Publisher index: 56 per-country HDF5 hazard files (28 countries × REF/PGW), 2.2-km model data, 19.9 GB total, plus small metadata.csv (3.2 kB). The source `metadata.csv` lists original filenames, ISO3 country, REF/PGW, resolution, CLIMADA data type and v2.
- Publisher's listed original `metadata.csv` MD5: `6b6b1d4ec919f56ded7669da3f3b2b82`. **Not an independently checked SHA-256 or source signature**.
- Pilot file pairs and publisher-stated MD5 (not independently checked):
  - `hail_LUX_ref.h5`: 8.3 MB; `1d66d63e84d44565c35461c0b8457a57`
  - `hail_LUX_PGW.h5`: 5.6 MB; `2f92c82a25f73e33f93e494abbc2a610`
  - `hail_DEU_ref.h5`: 916.6 MB; `d4fdbacb9f68af041190a869cfb0cf8d`
  - `hail_DEU_PGW.h5`: 921.2 MB; `28f4054eaa7b62eb6468061741f13fe1`

## Acquisition and checks

The 2026-11-08 isolated Linux runtime could display original Zenodo catalogue/CSV via browser retrieval but could **not download its original bytes** by Python due to DNS resolution failure. No data, HDF5, real claims or source binary was committed. Do not falsely claim an original-byte validation.

1. Obtain the publisher's **original** `metadata.csv` outside the Git repository from https://zenodo.org/records/17860440/files/metadata.csv?download=1. Keep exact filename and no manual re-serialization.
2. Run `python research_runners/zenodo_hail330_metadata_preflight_v0.py /outside-git/metadata.csv`. This checks the exact publisher MD5 (blocking by default), CSV schema, 28 paired ISO3 country records and 56 release filenames; it prints a SHA256 of **the acquired local CSV bytes**, not the HDF5.
3. If the original metadata check passes and release-specific **commercial, redistribution, derivation and attribution rights** are reviewed, acquire one **Luxembourg** REF and PGW HDF5 outside Git. Check the exact publisher MD5s and record independently calculated SHA256, HDF5 groups/datasets, resolution, geographic coordinates, hail intensity units and nodata.
4. Before using as probabilistic catalogue, confirm annual-event grouping, original event family IDs, stochastic weights, spatial resampling assumptions, and whether events crossing national borders retain common parents. `330 years` is a spatially resampled exposure-hazard experiment, **not 330 independent observed/modelled weather years**. Never concatenate country files as independent losses or sum overlapping event IDs.
5. Link a **fictional** Luxembourg or Germany building portfolio, keep all modelled losses separate from observed insured claims, and compare deterministic hazard footprints in a small end-to-end test. No insurer-specific financial loss or OEP/AEP before full scientific and rights review.

The publisher website exposed a generic Rights section without a machine-verifiable file-license statement in the inspected text. **Do not infer CC BY from the open-access paper**: model source remains `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, and `admission_status=not_admitted`.

## What the metadata preflight does not prove

It does not prove that the 56 listed HDF5 files were retrieved, that their MD5s match, that they encode 330 annual years consistently, or that damage/vulnerability/insured exposure data are valid. All negative source gates remain blocking. The author's source MD5 is a file-integrity comparator, not a cryptographic signature or an approved licence.

Unit tests: `python -m unittest discover -s tests -p 'test_zenodo_hail330_metadata_preflight_v0.py' -v`. All unit-test inputs are synthetic, never original publisher rows.
