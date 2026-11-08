<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MaterialCities 2026.9 ADM2 regional floor-area preflight

## Exact source

- Provider: MaterialCities research consortium / Zenodo
- Public record: https://zenodo.org/records/22306604
- Release: **2026.9**, 8 September 2026
- Product: **MaterialCities_adm_gfa_csv.zip**, reported original publisher MD5
  098f04f9b204d3102165ba4b3e2b8520 (5.4 MB ZIP in record listing).
- Canonical discovery ID: leiden.materialcities.global-floor-material-stock.2026-9
  in landscape/sources-material-flood-insurance-priors-20261108.json.
- Original files and any source-derived regional output must stay **outside Git**
  until exact original-version rights, underlying geographical source terms,
  reproducibility, scientific use and publication scope have been reviewed.

The publisher describes modelled **gross floor area** by residential and
nonresidential building functions (NR, RS, RM) and construction-structure
types (C, M, T, S, U). The GFA ADM files use GADM 4.1 geographical
lineage. These are modelled *regional* quantities, not actual geocoded
buildings, claims, insurer-held sites, insured values, structural vulnerability,
or earthquake fragility curves.

## Bounded technical use

Once the licence and access terms for a local research evaluation have been
separately confirmed, obtain the original ZIP using an authorized provider
download path and record its provenance outside Git. Run:

    python -m research_runners.materialcities_adm2_gfa_preflight_v0 --archive /external/MaterialCities_adm_gfa_csv.zip --country DEU --out /tmp/materialcities-deu-adm2-gfa-receipt.json

Omit the country argument to inspect available ADM2 regions globally. The
preflight requires the published ZIP MD5, records SHA-256, rejects unsafe ZIP
members, requires complete source GFA function/structure fields and nonnegative
finite values, catches duplicate ADM2 IDs and reports, without silently fixing,
source GFA/structure breakdown disagreements. This is a source **schema and
consistency research receipt**; it is not approval for ingestion, consumer
simulation or public redistribution.

The preflight intentionally does **not** merge MaterialCities with Overture,
the R+V synthetic OED export, actual insured buildings or any private database.
A spatial join needs independently reviewed GADM/version identity, no
duplicate-counting across ADM0/ADM1/ADM2, uncertainty calibration and source
rights. A country GFA is not one insurer's TIV; modelled building typology
cannot directly be assigned as ground-truth stock or wind/flood vulnerability.

## Test evidence and blockers

Synthetic tests are provided in
tests/test_materialcities_adm2_gfa_preflight_v0.py. Run:

    python -m unittest discover -s tests -p 'test_materialcities_adm2_gfa_preflight_v0.py' -v

No original MaterialCities archive was downloaded or processed during initial
implementation. Until a legally permitted exact-source replay is executed and
verified, do not claim original data rows, ADM2 coverage, model calibration,
geographic matching, or portfolio/model readiness.

Source/provider rights review, additional GADM upstream terms, exact source
columns, source-region consistency and independent vulnerability validation
remain pending. Metadata-only discovery is the only approved state.
