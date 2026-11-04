<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Loing May/June 2016: observed high-water marks as independent field validation candidates

**Reviewed 2026-11-04. Research only; no new source admission or original external data file stored in Git.** This source analysis is narrower than the broad geographical Loing/CEMS event and does not assert ownership, redistribution rights for source photography/geodata, or any building-level flood depth.

## Two real provider records inspected, not invented synthetic markers

The [French government national flood-mark platform](https://www.reperesdecrues.developpement-durable.gouv.fr/) preserves verified first-party public HTML record pages, linked event/mark identities, physical evidence class, river, location, original field-survey method and **vertical datum**.

| Official page | Event (not surveying date) | Physical type | GPS leveling date | Relative survey reading | Published 2016 flood-water surface elevation |
| --- | --- | --- | --- | --- | --- |
| [Montargis, Commissariat de police](https://www.reperesdecrues.developpement-durable.gouv.fr/site/commissariat-de-police-0), site `CER_LO_16_S_174`, mark `CER_LO_16_R_174_1` | **2016-06-01** | `Laisse d'inondation` – field trace | **2016-06-08**, Cerema Normandie-Centre | Surveyed mark itself as vertical reference: **85.557 m NGF IGN 1969**; no separate offset stated | **85.557 m NGF IGN 1969** |
| [Ecluse d'Ecuelles, Moret-Loing-et-Orvanne](https://www.reperesdecrues.developpement-durable.gouv.fr/site/ecluse-decuelles), site `SMYL16_01_S_196`, mark `SMYL16_01_R_196_1` | **2016-06-02** | `Laisse d'inondation` – physical trace on bench/vegetation | **2016-09-01**, DRIEE / SPC Seine moyenne–Yonne–Loing | Bench/reference **50.531 m NGF IGN 1969** plus **0.250 m offset** to water | **50.781 m NGF IGN 1969** |

The exact elevation arithmetic was checked with a separate, manually entered two-record in-memory research sample against the [new strict offline source QA](../../research_runners/loing2016_high_water_mark_preflight_v0.py): **2/2 original-provider-page field identities and reference-elevation calculations passed**, no model flags upgraded. This is **HTML-source semantic reconciliation**, not original HTTP response SHA-256 verification. No source-point collection or observation data bytes were imported into production or committed in the tests. WGS84 coordinates for both are provided in the linked original government records and were checked within the test's geographically bounded Loing envelope; no coordinate-bearing third-party table is published here.

### Critical height semantics

1. **Event time is not field survey time.** The June 2016 flood marks were GPS-levelled *after* the event (8 June and 1 September respectively). Surveying the residual trace later can still help reconstruct a maximum; it does not give an instantaneous 2016 measurement time series or exact time of river crest.
2. **Vertical datum is mandatory.** Both records explicitly use `NGF IGN 1969 (système normal)`. A different datum, unknown height reference, GPS ellipsoidal height or HIXnJ station-relative gauge height cannot be directly subtracted or merged without a separately verified conversion. Coordinates in WGS84 are horizontal georeferencing, not proof of vertical datum.
3. **Reference offset is not inundation depth.** At Ecuelles, 0.250 m is the **water-mark level above the levelling reference bench**. It does not measure water above terrain at a building. A valid building depth requires a local and temporally matched terrain/threshold elevation in the same vertical datum and approved hydraulic spatial interpolation.
4. **Published decimal precision is not guaranteed survey accuracy.** The records show three decimals but no independent survey uncertainty budget was established here. Do not infer millimetric accuracy or use the marks to create point-level zero-variance likelihoods.
5. **Mark evidence classes differ.** A documented physical `Laisse d'inondation` is stronger field evidence than a 2016 oral testimony with a later GPS-located site. The [Montargis Sous-préfecture entry](https://www.reperesdecrues.developpement-durable.gouv.fr/site/sous-prefecture) is explicitly `Témoignage oral`: valid *context* but not interchangeable with a surviving physical trace. Likewise [Souppes-sur-Loing Quai de la gare](https://www.reperesdecrues.developpement-durable.gouv.fr/site/quai-de-la-gare) gives a published water figure yet does **not** explicitly state the same vertical datum in the accessible page; exclude from this strict NGF1969 pilot unless verified elsewhere.

## Direct link to the 2016 Loing Aval flooded-area and water-depth atlas

The [official Préfecture du Loiret PPRI/AZI page](https://www.loiret.gouv.fr/Actions-de-l-Etat/Securite-et-risques/Securite-civile-risques-et-protection-des-populations/Prevention-et-gestion-des-risques/Risques-Naturels/Inondations/Plan-de-Prevention-des-Risques-d-Inondation-PPRI/Le-PPRI-de-l-Agglomeration-Montargoise-et-Loing-Aval) has an explicit section titled **`Le Porter à Connaissance n°1 sur l'Atlas des zones Inondées (AZI) du Loing Aval en 2016`**. It links three methodology annex PDFs (published **2021-12-15**) and **14 commune-specific May/June 2016 water-height map PDFs** across Amilly, Cepoy, Châlette-sur-Loing, Corquilleroy, Dordives, Ferrières-en-Gâtinais, Fontenay-sur-Loing (two sheets), Girolles, Montargis, Nargis (two), Pannes and Villemandeur.

Exact primary official PDF links for one bounded pilot:
- [AZI Loing 2016 methodology, Annexe 1](https://www.loiret.gouv.fr/contenu/telechargement/54073/372059/file/Annexe%201.pdf) – published PDF size **14.58 MB**, according to official page; source contents not byte-audited in this review.
- [AZI Loing 2016 methodology, Annexe 2](https://www.loiret.gouv.fr/contenu/telechargement/54072/372055/file/Annexe%202.pdf) – **5.59 MB**, as listed.
- [AZI Loing 2016 methodology, Annexe 3](https://www.loiret.gouv.fr/contenu/telechargement/54071/372051/file/Annexe%203_20211116.pdf) – **6.51 MB**, as listed.
- [AZI_2-09_MONTARGIS water-depth map](https://www.loiret.gouv.fr/contenu/telechargement/54061/372011/file/AZI_2-09_MONTARGIS_compressed.pdf) – **3.15 MB**, listed 2021-12-15.

These source URLs and sizes were checked through the actual government **HTML index**; **the embedded original PDFs and any underlying GIS features were not downloaded or checked**, and a PDF picture is not a validated original geospatial data file. **Do not conflate this retrospective 2016 AZI atlas** with the separate 2023/2024 statutory PPRI flood hazard/zoning layers or with the pre-2016 hypothetical Vigicrues ZIP/ZICH stage scenarios.

An official later PPRI account notes that some original **1 June 2016 orthophotos were taken ~10–24 hours after the peak** in the lower Loing and may omit peak-water extent. A reconstructed atlas must declare whether its modeled/estimated depths derive from contemporaneous SAR/optical imagery, high-water marks, elevation models or hydraulic extrapolation; no independence claim is made before its exact annex methodology is parsed.

## Implemented falsifiable evidence gate

[The standalone Python preflight](../../research_runners/loing2016_high_water_mark_preflight_v0.py) is **offline**, rejects unknown/non-official site URLs, wrong Loing event dates, separate GPS survey timing errors, unknown vertical datums, invalid coordinates, impossible or nonreconciled reference+offset elevations and duplicate mark/site identifiers. It distinguishes a self-levelled physical mark (no invented 0.000 m offset) from another levelling bench with an explicit offset. Oral testimony remains a weaker nonphysical evidence class. The original platform must additionally label **maximum of the flood = yes**: a nonmaximum physical trace may document flooding but is **not** a candidate peak-water validation observation. The dedicated boolean is type-checked (numeric 1 is rejected), and the returned candidate flag is false when the source reports a nonmaximum. **14 synthetic offline regression tests**, runnable with:

```sh
python -m unittest discover -s tests -p 'test_loing2016_high_water_mark_preflight_v0.py' -v
python scripts/check_all.py
```

The preflight's arithmetic success never implies original provider-byte authenticity, an accuracy model, source/third-party geodata rights, a flood-water height transformation, parcel ground elevation, building flood-depth or insured CAT loss admission. No actual marks are committed as original provider-data fixtures, and no production or private DB was modified.

## Scientific next step

**Montargis 2016 Loing pilot**: obtain one rights-reviewed exact original cartographic 2016 AZI Montargis PDF and its methodology annex, pin byte size and SHA-256 outside Git, determine its coordinate/vertical reference, legend/depth methodology and whether a usable original GIS layer exists. Select independent recorded high-water marks *before* inspecting model residuals, establish surveyed ground/mark uncertainty and timestamp, and derive a spatially varying simulated water-surface field from a physically justified hydraulic model. Compare model vs **observed 2016 flood surface elevations** at those exact locations; never directly equate the published mark to a property depth.

If comparing CEMS Rapid Mapping, also preserve one exact **EMSR165 DEL AOI** and original sensor acquisition time. The separate [EMSR165 research PR](https://github.com/pokekarten/OpenCatastrophe-data/pull/1263) does not certify overlap with Montargis and does not license/API-authorize acquisition. Compare only after spatial and chronology compatibility is proved.

**Verdict:** two original government flood-mark pages now provide research-level 2016 NGF1969 surveyed water-surface reference candidates and a specific official 2016 AZI water-height atlas is identified. Full geodata/data-rights/uncertainty/source-byte proofs and model validation remain open.
