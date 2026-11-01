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
