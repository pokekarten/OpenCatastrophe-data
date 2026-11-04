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
