<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Full-in-query-box official Berlin ALKIS vs LoD2 2022 geometry and height audit

## Why this is the correct next source step

Prior independent live official WFS2.0 count-only source proof
[run 41323901716](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323901716)
confirmed **18 ALKIS building features** and **27 Umweltatlas LoD2
2022 height features** in the same frozen 200m × 200m research box in
EPSG:25833 (UTC 2026-11-01T15:58:41+00:00). The earlier 5×5 first
features had zero one-to-one IoU≥0.95 matches, an
**incomplete-ordering artifact** that must not be used to conclude
that the height product lacks spatial correspondence.

## Strict source-specific complete extraction

`research_runners/berlin_alkis_lod2_complete_bbox_v0.py` performs
**one** official anonymous WFS GetFeature request per independently
reviewed source at fixed 200m bbox
`391700,5819950,391900,5820150,EPSG:25833`,
`count=50`, `outputFormat=application/json`, WFS2.0:

- `alkis_gebaeude:gebaeude` from official monthly ALKIS Berlin,
  <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>.
- `ua_gebaeudehoehen:gebaeudehoehen` from independent-source product
  Berlin Umweltatlas **2022 LoD2 height**, updated 2023,
  <https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d>.

Each HTTPS response is bounded by **768 KiB, 45 seconds, no redirects
or proxies**, and the code rejects unknown hosts, CRS, untrusted
queries, changed feature types, empty/malformed GeoJSON,
invalid/duplicate original feature identity, nonpolygon geometry,
nonfinite/invalid coordinates, unreasonable areas and out-of-scope
polygons. **Both original GeoJSON sources must explicitly declare
EPSG:25833**; the WFS request parameter alone is not proof of response
coordinate semantics. Topologically identical source footprints with different IDs may
represent actual building/part segmentation rather than invalid provider
records. They are therefore **counted as duplicate footprint groups and
quarantined together from all unambiguous one-to-one match candidates**,
rather than first-wins deduplicated or silently assigned a roof height.
Total source feature counts remain original, so duplicates are not
misrepresented as a reduced census.
Most importantly, it **requires source-provided integer
`numberMatched` and `numberReturned` to be equal to the actual
number of features returned**, with at most 50 features per source.
If the 2022/2026 live source data now have more than 50 features
in the same fixed study box, the research stops rather than claiming
a complete sample.

Once complete source sets exist in memory, the audit computes all
original spatial polygon intersections/union areas in the same
projected coordinate space. Only one-to-one original footprint pairs
with **intersection-over-union (IoU) ≥0.95**, with no conflicting
other matching candidate, count as unambiguous spatial matches.
This does *not* claim a permanent source identifier equivalence, 2022
to 2026 physical stability, actual replacement value, or insured
portfolio inclusion.

The source-only safe receipt includes all current in-box feature
counts, unmatched original feature counts, unique unambiguous polygon
pairs, candidate ambiguity, and **aggregate counts** for
`role_txt` (building vs Bauteil), `hoehe`, `dachart`,
`geschosse`, `quelle*` estimation methods and possible **3m
placeholder** roof heights. No raw source identifiers, geometry
coordinates, individual heights, addresses, attributes or provider
feature values are logged, saved, committed or transferred into
CAT/Neon/Pokémon databases. In particular no heights are admitted to
an insurer model by this research code.

For *only the uniquely matched polygon pairs*, the new non-admission
quality gate additionally reports aggregate known/unknown building/part
roles, positive numeric heights, exact 3m **possible placeholders**,
non-3m heights **not proven measured**, and the presence of source-method
codes. Even a recognized building role with non-3m height is only a
research-triage candidate: its identity, height method, source 2022/2026
vintage, scientific uncertainty and rights remain independently gated.
No individual height or provider source ID is printed.

The dedicated `.github/workflows/berlin-alkis-lod2-complete-bbox.yml`
runs source-free synthetic tests on PR; a reviewed workflow-file
change triggers **one** bounded real two-source experiment on main.
No nationwide recurring crawler or bulk downloader is enabled.

The results must distinguish official *feature* counts from unique
physical buildings. The 2022 LoD2 height product contains building
and building-part polygons and some 3m imputed first-height values;
an insurer property may overlap one or several source polygons.
Product vintages and original data rights (both official catalogues
list **dl-de-zero-2.0**) remain explicit. The height product reuses
ALKIS-related footprints upstream and is not an independent precision
ground-truth provider.

## Original-source result

Pending the first reviewed original WFS execution.
Only successful source-run evidence can establish the actual
complete-in-bbox polygon IoU and height/role counts. Synthetic tests
are *not* evidence of measured/verified real building heights.

## First-party full original-source reconciliation — 2026-11-01

The complete source-reported feature populations in the *same fixed
200m × 200m original source EPSG:25833 box* were independently
downloaded, checked and compared in
[GitHub Actions run 41324614040](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41324614040),
merged main commit `6dcab89bec98a7c8f0e8b43c3c212e0b4bf58d10`,
UTC `2026-11-01T16:07:01.947191+00:00`:

| Original-source evidence | Observed value |
| --- | --- |
| Current ALKIS original GeoJSON response | 20,880 bytes, SHA-256 `9f35b57dfcd3336f0cca5735850abb1fe88072de82d16c1163b1579cbce2d945` |
| Official Umweltatlas LoD2 2022 height GeoJSON response | 35,917 bytes, SHA-256 `63a0eeece2b10113016ea56d2e9474a671935bd2201e2dabcc535b3ebf11680f` |
| Independent original `numberMatched=numberReturned=features` | **18** ALKIS / **27** 2022 height features |
| Polygon validity / source CRS / count completeness | All implemented source gates passed |
| Unique one-to-one polygon matches (projected IoU≥0.95) | **6** |
| Ambiguous source candidate incidences at IoU≥0.95 | **3** |
| Not uniquely mapped original feature counts (includes ambiguous ones) | **12** ALKIS / **21** heights |
| `hoehe` positive numeric | **27 / 27** |
| `dachart`, `geschosse`, `grundrissaktualitaet`, `quellebodenhoehe`, `quelledachhoehe`, `quellelage`, `role_txt` non-null | **27 / 27** each |
| Recognized `role_txt` = Gebäude | **2** |
| Recognized literal Bauteil | **0** |
| Other/unrecognized role labels | **25** |
| Exact 3m height possible placeholder | **0** in this sample |
| New heights assigned to CAT4 or insured assets | **0** |
| Original geometry, IDs, addresses or attribute values persisted or logged | **No** |

The first-five 0-match result was a **sampling/order limitation**:
now **6** strictly unambiguous geometric pairings are observed when
testing the actual full 18 and 27 original feature populations.
This proves the overlap method can identify near-identical source
footprints, **not** that six physical insured buildings have independently
measured roof heights.

Do not reinterpret the **25 unknown role labels** as Bauteil or
Gebäude without checking the provider's actual source domain codes.
Ambiguous pairings may represent building-part segmentation and
data-vintage differences. Do not weaken IoU or silently match via
names, addresses or IDs. At most six **candidate** height assignments
exist for future controlled research; **none** have been admitted to
CAT4 or insurer portfolios. The next investigation should inspect
the official role/height-source domain semantics in aggregate, and
quantify coverage/splits before integrating any height attributes.


## Source-proven geometry duplicate blocker — 2026-11-01

After PR #1009 required topologically unique source footprints and
PR #1011 added matched-subset role/height QA, the dedicated original
[source run 41325287758](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41325287758)
**failed closed** at UTC `2026-11-01T16:14:44Z` with
`duplicate original source footprint geometry`. The previous
6 matching pairs were observed with an earlier code version, and
**must not be treated as revalidated under this stricter source gate**.

A source feature can legitimately be a building or its overlapping
part, or several features can share a complete 2D footprint. The
research now counts exact-geometry duplicate groups per source and
**quarantines all their members** from candidate 1:1 matches; it
neither deletes source features nor assigns those ambiguous roof
heights to an insured asset. The independent source population
totals remain 18 and 27 only as observed on the original receipt;
later real replies may differ. The first original rerun of this new
quarantine logic must independently verify the exact counts, source
CRS, duplicate groups and revised 1:1 matches before any updated
number is reported.

## Verified original duplicate quarantine, matched-subset height and role — 2026-11-01

The official [WFS source run 41326537234](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326537234)
on merged source commit `fc9ee78a853b9ffb7aa56174ef0b2e00c22d9736`
**passed** 10 synthetic tests and two original fixed Berlin WFS requests.
UTC source receipt `2026-11-01T16:29:05.448330+00:00`.

| First-party evidence | Actual bounded result |
| --- | --- |
| Source feature records | 18 ALKIS / 27 LoD2 |
| Source SHA-256, ALKIS | `3d8230fae323a454794558e93cc1bef3086ad3d1a4cda418875f6c02071172c2` |
| Source SHA-256, LoD2 | `5fa491c87072031f0e2803cfa5129da2586b60a96cd21817a8fdd6fe3510a763` |
| Distinct duplicate-footprint groups (LoD2) | **3 groups** |
| Total LoD2 source features quarantined | **6** |
| ALKIS duplicates / quarantined | 0 / 0 |
| Unique unambiguous source-polygon pairs after quarantine | **6** |
| Valid positive numeric heights on those six pairs | **6** |
| Exactly 3m values on six matched polygons | **0** |
| Recognized source role on six matched polygons | **0** (`unknown`: **6**) |
| Non-null source-method fields on six pairs | **6 of 6** each |
| Model-admitted / insured height assignments | **0** |

These figures concern **source polygon feature records**, not unique
physical buildings; no original feature attributes/coordinates were
persisted. Field presence is **not** proof that the underlying height
method was physical measurement rather than algorithmic LoD2 estimation.
The official technical guide labels `role_txt` as *Gebäude oder Bauteil*
but does not publish an exhaustive spelling/code vocabulary:
<https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_06_10_1gebhoehen.html>.
The publisher's method uses LoD2, ALKIS and a possible 3m fallback:
<https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/methode/>.

The next research lane is therefore a **bounded, non-identifying
vocabulary hypothesis check**, not changing unknown role assignments
to actual building/part classes. `CityGML` schema type names are
generic candidate spellings, not verified values from this publisher.
Only small aggregate exact-token category counts may be emitted, never
raw, unrecognized `role_txt` strings or other source attributes.


## Source-proven exact `Gebäudeteil` label — 2026-11-01

The official [two-source GitHub WFS run 41327637956](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41327637956)
on main commit `9c3d0f304884b7151c591f624ab533a16e2154f8`
passed **12 synthetic tests** and two original, fixed Berlin WFS calls,
receipt UTC `2026-11-01T16:42:04.164830+00:00`. Its
non-identifying exact-token source vocabulary checks found:

| Original `role_txt` spelling | 27 LoD2 source features | Six unique polygon matches | Six quarantined duplicate-footprint source features |
| --- | ---: | ---: | ---: |
| `Gebäude` | 2 | 0 | 0 |
| `Gebäudeteil` | **25** | **6** | **6** |
| `Bauteil` | 0 | 0 | 0 |
| Other/unrecognized terms | 0 | 0 | 0 |

Independent original response SHA-256: ALKIS
`5e1cfc47ecbdf82278d40a4c68bcd18be0ef3862577e0cff3481107a022ffc69`;
LoD2 `5e3ddd89dd40481d1a9a9b891649a7e7dba9f700cf4a3a681ce4a38f18a5cfc2`.

The former reported `unknown=25` was a **parser vocabulary
limitation**, not missing source roles. The official
[Berlin data dictionary](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_06_10_1gebhoehen.html)
describes the field as *Gebäude oder Bauteil*, but did not enumerate
actual emitted labels. Now the verbatim `Gebäudeteil` source literal
is separately recognized **without conflating it with the
`Bauteil` term or treating it as `Gebäude`**.

**All six IoU>=0.95 candidates are labelled building parts** in
the historic source and must not become six insured building
entities. Their height method, duplicate relations, 2022-versus-current
vintage, rights and scientific uncertainty all remain explicit.
No building ID, individual feature value or insurer CAT4 record
has been added.

## Method-code and descriptive-label coverage gate (research only)

The Berlin [technical data dictionary](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_06_10_1gebhoehen.html)
explicitly pairs `quellebodenhoehe` with `quellebodenhoehe_txt`,
`quelledachhoehe` with `quelledachhoehe_txt`, and
`quellelage` with `quellelage_txt`. The code alone does **not**
identify the physical measurement method unless the source code list
is independently reviewed and corroborated.

The new audit reports only aggregate **code-and-description presence**,
**code-only**, **description-only**, or **both absent** counts for
each of the three method fields across all LoD2 source features,
the unambiguous six polygon matches, and duplicate-footprint source
features quarantined from unique matches. Neither provider source
codes nor description strings are logged, hashed or exported. A code
value of zero counts as **present**, not missing. Unexpected nested
objects or nonfinite method values fail closed.

This is **not a correctness check of code↔description mapping**,
not a measured-versus-imputed height classifier, and not a proof that
all matched historical `Gebäudeteil` records are entire physical
insured buildings. The publisher states LoD2 heights are automatically
obtained using DOM/bDOM/DGM1 and may fall back to a 3m assumed height:
<https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/methode/>.
No insurer, CAT4 or production height values are admitted.

## First real code-and-description method coverage — 2026-11-01

The reviewed [first-party WFS run 41328878314](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41328878314)
after [PR #1027](https://github.com/pokekarten/OpenCatastrophe-data/pull/1027)
**succeeded** on exact merged main commit
`a967f4cffc9a5484f0bbd00c15c70c0f3f9e8c23`.
All **17 synthetic specialized tests** passed before the one fixed pair
of original official WFS requests. UTC receipt
`2026-11-01T16:56:46.632207+00:00`.

The exact original-source response SHA-256s were:

- ALKIS (18 features):
  `47b3e6f538bc1f044869ec13a1c67747bf92275646afa3f046ba865d445269cf`.
- LoD2 2022 (27 features):
  `f4fd22d07cd7a38e8fbd808bb73de2cf7798a272edefefb5603094c0c0288fc7`.
- Verified executed research script SHA-256:
  `2a735bf4b5bc6cd96145c5d7f188cf9375e9d7d11bab4f5702ce09f33729e1d5`.

| Original source method field | All 27 LoD2 records with code **and** description | Six uniquely matched `Gebäudeteil` footprints | Six quarantined LoD2 source records |
| --- | ---: | ---: | ---: |
| `quellebodenhoehe` + `quellebodenhoehe_txt` | **27/27** | **6/6** | **6/6** |
| `quelledachhoehe` + `quelledachhoehe_txt` | **27/27** | **6/6** | **6/6** |
| `quellelage` + `quellelage_txt` | **27/27** | **6/6** | **6/6** |

Across all three fields and populations, **no** observations
were classified code-only, description-only or both absent.
The source polygon comparison remains 18 ALKIS vs 27 LoD2, with
three quarantined exact-geometry groups (six original LoD2 records),
six unambiguous geometry matches, all matched as `Gebäudeteil`.
No source method values, height measurements, individual feature
identifiers, address/geometry values or original response bytes
were logged or written to the repository or insurer databases.

**Scientific interpretation:** present method codes and explanatory
labels are metadata **completeness**, not code↔label correctness,
independent measurement, absence of default imputation, historic
building identity or production suitability. In particular,
`hoehe != 3` does not imply a direct sensor measurement.
Before assigning calibrated uncertainty or a model-ready exposure,
the official method-code domains must be independently understood,
linked to DOM/bDOM/DGM1 methodology, rights reviewed and all
`Gebäudeteil` source identities handled at the appropriate
segmentation level. **CAT/model-admitted heights remain zero.**

## Empirical code↔description consistency review (not codebook verification)

The next audit computes *aggregate-only*, producer-source method
**internal consistency**, separately for Bodenhöhe, Dachhöhe and Lage.
For every method, within (1) all original LoD2 records, (2) uniquely
matched historical source-part polygons, and (3) quarantined duplicate
footprints, the audit reports:

- Number of observations with **both** code and description, distinct
  code groups, and distinct normalized description groups.
- How many code groups correspond to **multiple text descriptions**,
  and how many description groups correspond to **multiple codes**.
- How many observations are affected by either direction of potential
  inconsistency, without revealing which source codes or source texts.

Comparison trims/normalizes whitespace and letter case for text;
type-sensitive code grouping is intentionally conservative. No
method codes, descriptions, feature IDs, raw GeoJSON, stable hashes of
individual values or height measurements are exported or persisted.

**Crucial limitation:** one code consistently producing one label
does **not** establish that the label correctly interprets the
official AdV codebook, or that any height is a directly measured
observation. The Berlin [data dictionary](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_06_10_1gebhoehen.html)
names the fields but does not specify a complete numeric-to-text
codebook. The German AdV [LoD2-DE dataset description](https://www.adv-online.de/AdV-Produkte/Standards-und-Produktblaetter/ZSHH/Datenformatbeschreibung_LoD2-DE_V_3.19509.pdf)
references the separate AdV product-quality standard for source
method code semantics; no Berlin-specific field-to-codebook
equivalence is proven by this work. Any such mapping requires
distinct versioned legal, scientific and official provider reviews.

Neither a coherent code/description relationship nor positive
`hoehe` can establish the source method's precision or automatically
turn historical **Gebäudeteil** polygons into insured buildings.
CAT model admission remains false.

## First-party empirical method-code concordance — 2026-11-01

The reviewed post-merge [GitHub source run 41330142633](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41330142633)
on main commit `d98286d41ad0bae60ff0b08a17c2d13bd9bfe4c3`
**succeeded**. The fixed two-WFS source run followed **20 passing
source-specific regression tests** and issued no expanded geographic
request or extra provider call. UTC receipt:
`2026-11-01T17:11:07.111298+00:00`.

| Observed field, exact 200m pilot | All 27 original LoD2 objects: paired observations | Distinct code groups | Distinct description groups | Code→many texts / text→many codes |
| --- | ---: | ---: | ---: | ---: |
| `quellebodenhoehe` | **27** | **1** | **1** | **0 / 0** |
| `quelledachhoehe` | **27** | **1** | **1** | **0 / 0** |
| `quellelage` | **27** | **1** | **1** | **0 / 0** |

The identical **one-code / one-description / zero-divergence**
result also holds for each field separately among the **six**
uniquely matched LoD2 `Gebäudeteil` polygon records and the **six**
source-feature records in the three quarantined duplicate-footprint
groups. The original WFS populations remain 18 ALKIS vs 27 LoD2
sources; **six** unambiguous source-polygon matches; none admitted
as a whole insured building.

Original source receipt SHA-256s:

- ALKIS response:
  `665813ba53b71ea87babd29bcdffa44b8153ab382e7e9f7ee5ffa9f95a186235`.
- LoD2 2022 response:
  `6865a21f0aaf7e47fcdab53e09e1e11963190cfefe50d753c799ee89a708d6a0`.
- Research script:
  `f054bec71882588070bce37953b577370959bdf32439371014e1d1fc7c018684`.

**Limit of inference:** The lack of observed contradictions is not
strong validation of the dictionary: only *one method code per field*
was observed. Therefore multiple-code distinctions, imputed/estimated
versus measured categories and the correctness of any one code/label
pair remain **unverified**. Do not interpret one consistent method
label as a provider-approved source classification.

Next scientific gate: pin the exact version of the German AdV
**Produkt- und Qualitätsstandard 3D-Gebäudemodelle** code lists,
review the producer's field mapping to that standard and the Berlin
historic export, test code/text associations across independently
selected permitted sample regions, and distinguish measured, DOM/bDOM
derived, DGM-intersected and missing/imputed methods. No original
source code values or descriptions have been exported, stored or
logged; no CAT4/insurer portfolio height has been admitted.
