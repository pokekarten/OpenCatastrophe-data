<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MaterialCities 2026.9: exact-source ADM2 gross floor area preflight

## Provenance and reproducible source identity

- Original publisher: MaterialCities research consortium / Zenodo, release **2026.9** (2026-09-08).
- Exact record and licence statement: https://zenodo.org/records/22306604
- Actual ZIP member: MaterialCities_adm_gfa_ADM2.csv, inside MaterialCities_adm_gfa_csv.zip.
- Exact original ZIP length: **5,364,621 bytes**.
- Published ZIP MD5: 098f04f9b204d3102165ba4b3e2b8520.
- Independently observed original ZIP SHA-256: ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38.
- Metadata-only canonical candidate: leiden.materialcities.global-floor-material-stock.2026-9 in landscape/sources-material-flood-insurance-priors-20261108.json.

**Source inspection performed 2026-11-08:** The archived original provider ZIP
was acquired transiently in an isolated external Python 3.11 execution
environment from the official Zenodo content endpoint. MD5 matched the
published checksum and SHA-256 was recorded. No original ZIP, CSV row,
provider-derived region-value table, or geometry was added to this Git
repository or insurance database.

### Critical original source schema (corrects prior assumption)

The exact publisher 2026.9 archive has five CSV members: SSP5, SSP32, ADM0,
ADM1 and ADM2. The ADM2 CSV has **no standalone column named GFA**.
It contains exactly fifteen GFA-function-structure components
(function NR, RS, RM; structure C, M, S, T, U), plus GID_0/GID_1/GID_2
and other source fields. The sum of those fifteen modelled gross-floor-area
components is a **constructed source-row total**, not an independent
cross-check against another source-reported GFA measurement.

An earlier synthetic-only preflight incorrectly required a standalone GFA
column and would have skipped the authentic ADM2 file. The corrected reader
selects the literal publisher ADM2 CSV and treats absence of the standalone
total as the expected, version-pinned source schema.

### Research-only measured technical findings

The original ZIP and branch implementation were tested in a bounded,
byte-authenticated external Python run:

| Check | Result |
| --- | --- |
| Original archive SHA-256 / published MD5 | Exact match |
| Original ADM2 CSV rows | 47,874 |
| Distinct country/territory code values (source) | 251 |
| Germany (GID_0=DEU) rows | 402 |
| Germany source rows with unresolved/duplicate ADM2 key | 0 / 0 |
| Global source rows with noncanonical or unresolved ADM2 key | 1,064 |
| Global duplicate valid ADM2 key occurrences beyond first | 9 |
| Rows using special non-ISO Z01–Z09 GADM territory codes | 48 |
| Invalid/nonfinite/negative GFA component values on original scan | 0 |

The 1,064 unresolved/noncanonical rows include **778 with source
GID_2=0**, one with GID_2=?, and **285 Ghana-style source IDs**
such as GHA1.1_2 which do not meet the strict GADM canonical ID
pattern. The 9 duplicate valid IDs include several actual repeated
source keys. These are scientific identity flags, **not permission** to
discard, substitute, sum or deduplicate source rows into unique assets.
An unresolved key may still refer to a real administrative entity; it
requires independent, exact-version mapping evidence.

The 402 German source ADM2 rows are valid **as source-row identities**,
not geocoded buildings, policies, insured locations, carrier exposure or
CAT loss model observations. The source is a modelled building stock.

The original **German three-level internal reconciliation** was also tested
from the exact same byte-pinned ZIP: one ADM0 record, 16 ADM1 records and
402 ADM2 records, with the sum of all 15 GFA components approximately
12,143,344,605.93 square metres at **each** level (rounding differences
below 0.01 square metres). This proves arithmetic aggregation consistency
within one published source snapshot only. It is **not independent evidence**
that this is the real German built floor area, replacement value or insurer TIV.


## Running the corrected offline preflight

After separately confirming lawful source access for your specific use,
acquire the publisher ZIP outside Git and run:

    python -m research_runners.materialcities_adm2_gfa_preflight_v0 \
      --archive /external/MaterialCities_adm_gfa_csv.zip \
      --country DEU \
      --out /tmp/materialcities-deu-original-research.json

Omit the country flag to analyze the global source rows, but always inspect
complete_unique_region_keyset, source_rows_without_unique_adm2_key,
duplicate_key_occurrences and non_iso_source_country_rows. The
source-row gross floor area is not a unique-asset or TIV estimate.
The script rejects invalid source checksums, missing or altered ADM2
structure, unsupported ZIP entries and malformed numeric cells. The
reported research receipt has all admission, commercial-use and insurer
identity claims set to false.

No source-derived receipt needs to be committed to the public repository.

### Licensing and scientific blockers

Zenodo records the MaterialCities 2026.9 dataset as **CC BY 4.0**. However,
its ADM identifiers and boundaries derive from **GADM 4.1**, whose official
licence limits use to academic/other noncommercial purposes absent prior
permission and disallows commercial use or redistribution without permission:
https://gadm.org/license.html

Do not assume the Zenodo licence resolves GADM's independent upstream
rights. Commercial insurer uses, derived geographic products and redistribution
must remain **not reviewed / not admitted** until the source-specific rights
chain is resolved. The source may still inform a future carefully licensed
regional building stock prior, but it cannot itself allocate R+V's actual
insured locations, construction types, TIV or vulnerability.

No model/vendor engine runs, insurer-site joins, market-share estimation,
Neon database writes or actual R+V portfolio enrichment are established here.

### Test execution

The corrected exact-source implementation has **15/15 synthetic regression
tests PASS** in an independent Python 3.11 environment. Cases challenge
source absence of GFA, checksum spoofing, source member identity,
GADM sentinel and duplicate IDs, special territory codes, noncanonical
Ghana identifiers, invalid/corrupt numeric cells, ZIP paths and invalid
country filters. Run:

    python -m unittest discover -s tests -p 'test_materialcities_adm2_gfa_preflight_v0.py' -v

Repository-wide public CI remains the merge authority for this code.
