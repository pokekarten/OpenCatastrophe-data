<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: Apr GeoBase vs Nov BD-Adresses original address ID comparison

**2026-11-04.** This is an original-source, *non-admission* experiment,
following merged [PR #1292](https://github.com/pokekarten/OpenCatastrophe-data/pull/1292)
(GeoBase 2026-04 Addresses) and [PR #1287](https://github.com/pokekarten/OpenCatastrophe-data/pull/1287)
(CACLR/Geoportal ↔ GeoBase 2026-10 Buildings literal ID join rejected).

## Precise question

Are the official **2026-04 GeoBase Addresses** fields
`AD_AddressID` and `AlternativeIdentifier` related, via exact string
equality, to **2026-11 BD-Adresses** fields
`id_geoportail` and `id_caclr_bat`, respectively?
Both are address sources from the same ACT family, **not independent truth**.
The 7-month difference prohibits calling unmatched text "new/demolished"
buildings or inferring that stable physical entities have changed.

The official [ACT GeoBase contents specification v1 §4.1](https://download.data.public.lu/resources/bd-l-geobase/20240925-163507/contentsdescription-bd-l-geobase-v1.pdf)
calls `AD_AddressID` a unique GeoBase address feature ID and calls
`AlternativeIdentifier` a CACLR-supplied identifier. This does **not**
declare an equivalence to CSV fields without empirical proof.

## Immutable original sources

| Source | Exact frozen SHA-256 | Expected original population |
| --- | --- | ---: |
| GeoBase Addresses 2026-04-01 original ZIP | `edaf17ed2c802c155fd75caecfe44cbd23581a4b0a59f25935fa2d71a5e0b2eb` | 179,024 |
| Inner GeoBase `AD_Address` GeoPackage | `b357e7aa76a61ecabee45df28d68f3cdbce4ecdebf6f396d4d83ad2ba648fc12` | 179,024 |
| BD-Adresses 2026-11-02 original CSV | `f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c` | 179,768 |

The standalone job uses only these approved fixed original URLs and
reuses existing SHA/MD5/byte-size/GeoPackage safety proofs. It never
prints any row, original ID, location, personal address text or source
geometry, exports no original assets and persists no crosswalk.

## Measurable diagnostics

1. Each source column's nonblank/distinct/multiplicity aggregate count.
2. Exact distinct text-string intersections and total rows represented
   on either side, **including** multirow identifiers.
3. Exact ordered **address ID + alternate ID pair** intersections across
   publications. This is stricter than overlap of either key separately.
4. Explicit `cross_vintage_unchanged_identity_proven=false` and
   `address_to_geobase_building_crosswalk_proven=false`.

If any shared ID or pair appears, it is evidence of an overlapping
*identifier candidate*, not an independently surveyed address or
same physical building across time. Missing/extra IDs cannot be called
deleted or new source features without independent temporal proof.

**Execution status:** this page is a predeclared contract. Report
real overlaps only after exact-head original-source GitHub run completes.

## Actual complete-original source result (2026-11-04)

The exact-head [original-source Actions run 41891420321](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41891420321)
passed **all 10 synthetic negative/positive tests**, verified full SHA-256 of
both frozen official releases, and compared the actual original national
address-feature identifiers. No original ID, address, location, pair,
geometric record or source file was exported from the ephemeral runner.

| Original source key population | Distinct nonblank IDs | Duplicate excess |
| --- | ---: | ---: |
| 2026-04 GeoBase `AD_AddressID` | **179,024** | 0 |
| 2026-04 GeoBase `AlternativeIdentifier` | **178,431** | 593 |
| 2026-11 BD-Adresses `id_geoportail` | **179,768** | 0 |
| 2026-11 BD-Adresses `id_caclr_bat` | **179,184** | 584 |

| Cross-release exact-text comparison | Distinct shared identifiers | April rows involving shared keys | November rows involving shared keys |
| --- | ---: | ---: | ---: |
| `AD_AddressID` ↔ `id_geoportail` | **0** | 0 | 0 |
| `AlternativeIdentifier` ↔ `id_caclr_bat` | **178,254** | **178,845** | **178,837** |
| Complete two-key ordered pairs | **0** | 0 | 0 |

For CACLR-aligned alternative IDs:

- **177,709** distinct shared identifiers occur exactly once on **both** sides.
- **545** distinct shared identifiers occur more than once on at least
  one side; they MUST remain ambiguous one-to-many or many-to-many
  candidates until a separately evidenced disambiguation step.
- **177** distinct April alternative IDs have no exact counterpart
  among November CACLR identifiers.
- **930** distinct November CACLR IDs have no exact counterpart
  among April alternative identifiers.
- The intersection **178,254 / 178,431 = approximately 99.9%** of
  April alternative identifiers. The reverse coverage is lower
  because November's source population is larger.

**Conclusion:** the April GeoBase `AlternativeIdentifier` and November
`id_caclr_bat` share a highly reproducible **CACLR-style text namespace**,
whereas the purported `AD_AddressID` ↔ `id_geoportail` equality
hypothesis has **zero** exact matches. Their ordered two-key pairs
therefore also have zero matches. A literal CACLR key is an excellent
*cross-release address-record candidate* but is **not** an authoritative
statement that the corresponding building or insurance risk is identical.

**No seven-month lifetime claim**: IDs absent on one side may reflect
release differences, source coverage, data quality, address semantics,
different versions, or genuine change, which this comparison does not
adjudicate. The same ACT producer family means neither source is
independent ground truth. Do not coerce IDs, infer construction/demolition
or transfer insurer exposures based on this table.

### Next research acceptance gate

Confirm official CACLR `AlternativeIdentifier` semantics for duplicate
building-level IDs, then test the **177,709 singleton-key candidate pairs**
against independent address-semantic field agreement, source-vintage
validity and cross-CRS positional consistency. Preserve the 545
non-unique CACLR values as unresolved multi-address candidates; an
independent holdout and explicit address-to-building footprint
geometry proof are necessary before a CAT model input proposal.
