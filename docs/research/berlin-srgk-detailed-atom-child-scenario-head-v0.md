<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed SRGK: exact Atom child / three scenario ZIP manifests

**Research only — source ZIP bytes, TIFF metadata, pilot pixel coverage,
physical flood depths and insurer CAT modelling are NOT admitted.**

## Previously original-verified upstream evidence

[PR #1106, original root Atom run 41363918615](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363918615)
proved one fixed public `https://gdi.berlin.de/data/ua_srgk/atom/`
Atom root, 3293 original bytes, source SHA-256
`471becbd22ba5a862133ce0d59ed32981ccd30e44e3c7650b95d745d2c9d5eb4`,
one dataset entry and four metadata links, *zero direct ZIP links*.
The root's dataset alternate link identifies EXACTLY
`https://gdi.berlin.de/data/ua_srgk/atom/0.atom`.

Our second independent detailed-model-area pilot has a source-side
FES `geom` 40,000 m² positive original intersection, EPSG:25833
`[391860,5816840,392060,5817040]`,
[PR #1104 original run 41363537076](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363537076).
This is an official *model area* proof, **not proof any child ZIP contains
that region or particular scenario**.

## Exactly published child source contracts

The original provider **child Atom metadata** advertises these
three distinct named water-level scenario links, each with
`rel=section`, `type=image/tiff`, but an actual **`.zip` URL**:

| Scenario family | Exact official ZIP URL |
| --- | --- |
| Rare (`selten`) | `https://gdi.berlin.de/data/ua_srgk/atom/wasserstand_seltenes_ereignis.zip` |
| Extraordinary (`aussergewoehnlich`) | `https://gdi.berlin.de/data/ua_srgk/atom/wasserstand_aussergewoehnliches_ereignis.zip` |
| Extreme (`extrem`) | `https://gdi.berlin.de/data/ua_srgk/atom/wasserstand_extrem.zip` |

**The original Atom child states explicitly:** the extreme-event
water level is not available for every detailed-model area. The
Berlin 2026 [official source description](https://www.berlin.de/umweltatlas/wasser/starkregen/fortlaufend-aktualisiert/kartenbeschreibung/)
describes rare / extraordinary / extreme events, but different
study areas and vintages may not have comparable scenario rasters.
Do not infer equal spatial availability or assign probabilities
independently of a model version and rainfall contract.

### Rights distinction is mandatory

The official feed includes **German Data Licence Zero 2.0** plus
**area-specific CC BY 4.0 with mandatory attribution** for Moabit
and Flughafensee (Berlin Water Utilities). The global
[Geoportal metadata](https://www.geoportal.de/info/8de38448-67c9-3372-9f09-13cf33be4f86)
specifies a more detailed source attribution split for some areas.
A single ZIP may contain multiple model areas; mixed rights cannot
be flattened to an unconditional "fully open" insurer dataset.
No product-by-product redistribution/admission permission is granted
by this discovery.

## Controlled actual source head-only preflight

`research_runners/berlin_srgk_detailed_atom_child_zip_heads_v0.py`
makes **only** two exact public Atom feed GETs and three exact
original-scenario ZIP **HEAD** requests. No ZIP GET, partial byte
fetch or provider raster rendering occurs. The root is pinned by the
actual immutable previous-root SHA, and its exact alternate link
must match `0.atom`. The child must have the same Atom ID,
three exact known source ZIP URLs, their MIME metadata, current
mixed-licence notice and the extreme-scenario availability warning.

Every source request is strict HTTPS, no proxy, no redirect,
35-second bounded timeout; XML size caps are 16 KiB root and
32 KiB child. Only Atom XML byte count, hash, scenario names/URLs,
HEAD HTTP status / declared size/media and refusal flags are
recorded. Original Atom bodies and ZIP/raster bytes are not saved.
A provider ZIP HEAD rejection does **not** imply the ZIP is absent;
such cases remain `UNVERIFIED_HEAD_REQUEST`.

Synthetic negative tests cover root digest drift, changed child
identity, scenario substitutions, duplicate missing links, altered
rights/warnings, DTD/entities, excessive response and no-GET-ZIP
source boundaries. PR CI runs offline; the original source operations
are permitted only on a separately reviewed workflow push-to-main
or explicit manual dispatch.

## Next source gates after this receipt

1. Check real ZIP headers/size and original available file manifest
   under an independently reviewed **bounded** sampling policy,
   never a massive blind download.
2. Link original child ZIP contents to the second pilot via
   raster-index extents and correct CRS transformation, then prove
   original scenario/vintage and explicit physical water-depth
   units, scale, masks and NoData.
3. Review model-area-specific licence attribution and authorized
   reuse before importing any raw raster into isolated Neon CAT DB.
4. Only then pursue verified insured buildings, vulnerability,
   stochastic peril/event assumptions and a reproducible loss
   simulation; the independent BKG Int16 scaling issue #1086
   remains unresolved and must **not** be carried across to
   this separate detailed Berlin model.
