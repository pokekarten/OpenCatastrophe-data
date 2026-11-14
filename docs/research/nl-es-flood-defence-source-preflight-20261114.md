<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Netherlands NBPW and Spain SNCZI flood-defence source preflight (2026-11-14)

**Research only. No admission, no protected-area inference, no insured risk reduction, no raw provider bytes in Git or Neon.**

## Why these two products fill a different gap

The coarse global levee inventory and the newly registered England AIMS /
USACE NLD sources do not describe primary Dutch flood-defence trajectories or
Spain's official inventory of longitudinal river works. Those government
products are useful for a country-specific hydraulic defence test and a later
OED/Oasis spatial join, **only after independent data and rights review**.

## Exact official publisher evidence

| Source | Catalogue and rights evidence | Original data endpoint | Observed access scope |
|---|---|---|---|
| Netherlands NBPW (Informatiehuis Water) | [Nationaal Georegister record](https://www.nationaalgeoregister.nl/geonetwork/srv/api/records/fa4cc54e-26b3-4f25-b643-59458622901c) states no use restrictions, public access and ongoing coverage; legal text must be tied to the exact download | [Rijkswaterstaat OGC WFS](https://geo.rijkswaterstaat.nl/services/ogc/wvp/nbpw/ows/wfs) layer `nbpw:nbpw_dijktrajecten_formeel` | Intermediary requested precisely `count=1` and returned a FeatureCollection containing one MultiLineString feature on 2026-11-14; **not a trusted runner, not a stored original**, and not proof of feature completeness |
| Spain IOL (MITECO / SNCZI) | [datos.gob.es official INSPIRE catalogue](https://datos.gob.es/es/catalogo/e0dat0002-inventario-de-obras-longitudinales) shows public access, CC BY 4.0 reuse label and distribution creation in 2021 | Official source lists [ATOM](https://www.mapama.gob.es/ide/inspire/atom/downloadservice.xml), [IOL ZIP](https://www.mapama.gob.es/app/descargas/descargafichero.aspx?f=iol.zip), [IOL WMS](https://wms.mapama.gob.es/sig/agua/IOL?service=WMS&request=GetCapabilities) | A research fetch of WMS GetCapabilities did not deliver a parsable capabilities response (XML content-type unsupported by the intermediary); **no successful original API or ZIP byte test claimed** |

For the Dutch original WFS a tiny JSON sample was **viewed** in the external
research intermediary, not persisted: coordinates appeared in the range of
hundreds of thousands, consistent with **EPSG:28992 (RD New)**, despite
`application/json` / GeoJSON output. Treating such coordinates as WGS84
longitude/latitude would be a major geospatial error. Verify the actual
advertised WFS CRS, axis ordering and response-version semantics with the
original provider before any geometry pipeline.

Spanish IOL describes **both** flood-defence structures and bank-stabilisation
works. The existence of a riverbank work is not evidence of an effective flood
barrier, a crest height, a defended polygon, a breach model or design return
period. Dutch normative primary dike trajectories similarly do not establish
event-conditional protection reliability or local hazard depth changes.

## Bounded next original-source checks

1. Dutch WFS: exact original GetCapabilities + DescribeFeatureType for
   `nbpw:nbpw_dijktrajecten_formeel`; explicitly pin version, CRS, field names
   and licence reference. Use no arbitrary input, a byte cap, no redirects,
   single request, and publish only a response digest and schema summary.
2. Dutch feature: select at most one geometry after an authorized scope review,
   validate EPSG:28992 axis interpretation, topology, source update vintage
   and relationship to dike standard. Do not commit the feature.
3. Spain: first verify a bounded WMS/ATOM metadata response and its content
   type. Then inspect the official `iol.zip` HEAD or safe range/central-directory
   metadata with provider authorization and output size limits. Do **not**
   download the entire archive automatically.
4. Review exact commercial modelling, derived-value redistribution, attribution
   and any upstream third-party rights independently for both products.
5. Test a historical flood depth against both raw- and protection-aware hazard
   maps; avoid double-counting mitigation already in upstream inundation grids.

The canonical candidates are recorded in
[`landscape/sources-nl-es-flood-defence-20261114.json`](../../landscape/sources-nl-es-flood-defence-20261114.json).
Both remain `not_admitted`; this note does not authorize a consumer pipeline.
