<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# AdV PQS v2.4 candidate code lists: versioned historical building method reference

**Official source:** AdV *Produkt- und Qualitätsstandard für 3D-Gebäudemodelle*,
**version 2.4, prepared 2023-03-23**,
<https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/lod1-de_produktstandard%20_fuer_3d-gebaeudemodelle.pdf>.
Printed Annex 1 §2.13.4, pp. **11–12** lists numeric method source
codes for roof height, position, ground height; §2.14.5, p. **25**
confirms the corresponding quality attributes for LoD2.
The official AdV [3D model standards portal](https://www.adv-online.de/de/produkte/3d-gebaeudemodell)
links to the product standard.

| Historical Berlin source property | AdV PQS field | Candidate v2.4 codes |
| --- | --- | --- |
| `quelledachhoehe` | `DatenquelleDachhoehe` | 1000, 2000, 3000, 4000, 5000, 6000, 7000 |
| `quellelage` | `DatenquelleLage` | 1000, 2000, 3000 |
| `quellebodenhoehe` | `DatenquelleBodenhoehe` | 1000, 1100, 1200, 1300, 1400, 2000, 3000, 4000 |

**Caveat: Berlin Umweltatlas is 2022.** The [Berlin 2022 field
dictionary](https://gdi.berlin.de/data/ua_gebaeudehoehen/docs/Datenformatbeschreibung_06_10_1gebhoehen2022.pdf)
names these field pairs but does not establish that its historic
method codes obey this **2023** AdV version. The code sets above are
**external candidates**, not a verified Berlin producer crosswalk.
In particular, do not equate a possible roof laser-scan code with a
directly measured individual building height, or confuse DGM ground
sources with independent roof-height measurements.

`research_runners/adv_lod2_method_codes_v24.py` provides
`candidate_membership_counts`. It reports only the count of records
per field which match the 2023 candidate set, are missing, or are
unlisted/malformed. It keeps actual source codes, descriptions and
identifiers completely private to the in-memory process.
The fixed 200 m Berlin comparison reports these counts separately
for all historical LoD2 polygon records, the 1:1 matched historic
`Gebäudeteil` records, and duplicated polygons under quarantine.
No extra network requests, original bytes, spatial records, insurer
asset IDs, height measurements, stable source-code hashes or
persistent CAT/insurance/TCG databases are created.

**Next gate:** identify the producer-confirmed 2022 quality-code
edition and actual source-to-AdV field mappings, then verify method
semantics with permitted source evidence. Candidate membership
alone does not authorize a real-world measurement classification,
insured-building mapping, or risk/vulnerability/model admission.


## First original WFS code-list membership receipt — 2026-11-01

The official [original-source GitHub run 41331804324](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331804324),
on merged main commit `aa9d467ad8613bebfedf4c4358ff25dba6076da8`,
completed successfully with **26 synthetic safeguarding tests** and
two official, original, fixed 200 m Berlin WFS requests.
Receipt timestamp `2026-11-01T17:30:35.563137+00:00`.

| Field | 27 original historic LoD2 polygons: codes contained in 2023 PQS v2.4 list | Six uniquely matched historic `Gebäudeteil` footprints | Six source polygons excluded by duplicate quarantine |
| --- | ---: | ---: | ---: |
| `quellebodenhoehe` | **27/27** | **6/6** | **6/6** |
| `quelledachhoehe` | **27/27** | **6/6** | **6/6** |
| `quellelage` | **27/27** | **6/6** | **6/6** |

For all three fields and populations, neither *unlisted/malformed*
nor *missing* candidate-code buckets occurred. This says only
that the observed **2022 data source codes belong to the numeric
sets in the 2023 AdV reference**. It does not determine which specific
one code appears, whether Berlin used the same semantic interpretation
in 2022, whether roof heights were independently measured or inferred
from DOM/bDOM, or whether any building part is a whole insured building.

Exact original response SHA-256s:

- Current ALKIS polygon WFS:
  `1c539c4ffd5507f9b9b8d8a8504997126f703c7131d92eb858515df4758bfe09`.
- Historical LoD2 2022 height WFS:
  `cbc063a0650376e7f79aa4328edc3984a18bb96e639d69d3bbbfcf959cc043ae`.
- Exact executed research script:
  `cd094fad0df5ba2a240dc84e484187de43b1551b13709e7fab98bffbc04b24b3`.

The Berlin [publisher's original data-basis note](https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/datengrundlage/)
states that the underlying ALKIS footprints were current as of
**2022-04-07**, while our ALKIS WFS query retrieves the present-day
service. The AdV [2022 quality verification plan](https://www.adv-online.de/AdV-Produkte/Standards-und-Produktblaetter/ZSHH/binarywriterservlet?imgUid=54d40ca8-b795-9291-5dd8-f761533daed3&uBasVariant=11111111-1111-1111-1111-111111111111)
describes a version **3.0.0, dated 2022-03-10**, but is **not**
identified here as the exact historic Berlin product-standard
edition or a validated producer code↔text crosswalk. Do not
silently substitute that verification-plan version for the PQS
reference version.

The next required scientific lane is official producer confirmation
of the historical 2022 field mapping and release/version,
independent original samples with **multiple method categories**,
and documented license and measurement uncertainty review.
No CAT4 insurance exposure or individual roof-height record is
admitted.
