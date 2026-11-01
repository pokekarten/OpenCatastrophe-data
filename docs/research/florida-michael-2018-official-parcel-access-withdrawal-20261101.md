<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Florida 2017/2018 pre-event parcels: original FGDL withdrawal and sanctioned current FDOR alternative

**Live provider-check date:** 2026-11-01. **Status:** verified historical metadata plus current state spatial service metadata/aggregate only; **no historical parcel file**, no raw parcel rows, sensitive owner/address, insurer exposure, geospatial parcel polygons or individual FEMA assessment geometry retrieved or stored. This supersedes an earlier unverified hope of a normal FGDL 2017 archive ZIP download.

## Primary authoritative withdrawal discovered

The [University of Florida GeoPlan Center's own 2025-10-08 notice](https://www.geoplan.ufl.edu/parcel-layers-removed-from-fgdl-per-state-request/) explicitly states that **all** Florida Geographic Data Library (FGDL) parcel layers, **including historical versions**, were removed **at the request of the State Geographic Information Office (GIO)**. The notice has since been updated and remains publicly displayed.

This was corroborated by reviewing the [public FGDL archived ZIP index](https://fgdl.org/zips/geospatial_data/archive/), which still contains numerous unrelated historical layers but **no `parcels_2017` or `parcels_2018` ZIP listing**. The surviving historical metadata pages are [`PARCELS_2017`](https://fgdl.org/zips/metadata/htm/parcels_2017.htm) and [`PARCELS_2018`](https://fgdl.org/zips/metadata/htm/parcels_2018.htm). A historical metadata page or a former download pointer is **not evidence that the original ZIP is currently available or authorized via FGDL**.

| Former historical dataset | Original FGDL record | Current official FGDL data access | CAT model admission |
| --- | --- | --- | --- |
| `PARCELS_2017` | 10,086,830 parcel polygons; content 2017-09-26–2017-12-22; published 2018-01-19 | **Withdrawn on state request**; text metadata survives | **NO-GO**: no licensed original 2017 file verified; parcel polygons are not roof footprints |
| `PARCELS_2018` | 10,261,260 parcel polygons; content 2018-07-24–2018-12-28; published 2019-03-12 | **Withdrawn on state request**; text metadata survives | **NO-GO**: source content spans 2018-10-10 hurricane date and cannot be a pure pre-event snapshot |

**Do not guess hidden ZIP URLs, bypass the official publisher withdrawal or acquire an unreviewed mirror** just because the metadata remain indexed. Alternative historical packages from a county property appraiser or an officially authorized FDOR release would require a distinct current authorization/source identity, version date, license/security and original checksum review. The FGDL withdrawal does **not** itself prohibit every independently lawful Florida parcel dataset; it means the **specific removed FGDL archives are unavailable through that provider's current public distribution**.

## FGDL's officially referred Florida Department of Revenue replacement

GeoPlan recommends a separate, [official FDOR statewide cadastral FeatureServer](https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0), administered by the State of Florida and county property appraisers. The service's **original** current feature layer declares:

| Original source property | Provider-checked value |
| --- | --- |
| FeatureServer item ID | `efa909d6b1c841d298b0a649e7f71cf2` |
| Layer 0 internal name | `CADASTRAL_DOR` |
| Public map label | `FDOR Cadastral 2025` |
| Geometry | `esriGeometryPolygon` (land parcels, **not** buildings) |
| Geometry CRS | Spatial reference has state-oriented `wkid:102967`, `latestWkid:6439` in returned original JSON; the REST HTML extent displays 3086, illustrating the need to preserve original CRS/version details and not assume 4326 |
| Important source-native fields | `OBJECTID`, `CO_NO`, `ASMNT_YR`, `OWN_NAME` (the latter signals owner-identifying fields) |
| Authoritative service dataset vintage | State parcel polygon submissions from 2025, then maintenance; **no 2017 historical snapshot established** |
| Original read-only public API `/query` | `where=1=1`, `returnCountOnly=true`, `returnGeometry=false`, `f=json` |
| **Directly returned original count on 2026-11-01** | **10,950,670 source parcel polygons** (not unique houses) |
| Features and personally identifying source rows downloaded | **None** |

Both the state FeatureServer and the GeoPlan withdrawal statement explicitly warn about **confidential or exempt property-owner records**. Merely serving a public ArcGIS endpoint does not authorize unrestricted owner/address redistribution or demonstrate suitability for modeling an insured property. This project's audit uses only the original **schema** and one count-only aggregate. No source geographic point, parcel ID, owner field value, address or tax-roll file was read or copied. The live count is **not** an immutable source snapshot or original-data SHA-256.

The state product is **not** an interchangeable current `PARCELS_2017` file. It is a distinct statewide 2025-labeled annual cadastral dataset: original FGDL combined multiple source histories and standardized fields, whereas the official FDOR product directly reflects current state data and can include subsequent edits. The count difference from the historical metadata is **not evidence of Hurricane Michael building damage**, nor a count of additional demolished or constructed buildings.

## Reproducible access and scientific gate

`research_runners/florida_fdor_cadastral_access_gate_v0.py` implements two separate pure offline gates:
- `historical_access_gate()` records the official 2025-10-08 FGDL withdrawal for exactly `florida.fgdl.parcels-2017`/`2018`; refuses requests to treat an unverified FGDL historical ZIP as available or to substitute the current state service for historic pre-hurricane data.
- `validate_current_state_source()` accepts only a strict caller-supplied metadata-field projection for the exact current FDOR FeatureServer item and a `{"count": integer}` provider-style result, returning aggregate scientific warnings only. Source authenticity must be established separately from that offline code. Unreviewed feature/owner rows and forged count objects fail closed.

`tests/test_florida_fdor_cadastral_access_gate_v0.py` exercises withdrawn-source access, wrong vintage substitution, unexpected sensitive fields, wrong provider, and type validation using **synthetic** metadata and the individually observed aggregate count as a fixed test fixture.

**Next research priorities:** request an explicitly authorized official versioned historical dataset where available, beginning with a scoped Bay County 2017–2018 inventory *through legitimate current publisher routes*; investigate independently date-stamped building polygons instead of equating parcels to roof footprints; independently trace FEMA `RS` source imagery and compare against the exact NOAA alpha-mask negative receipt. No existing dataset is yet approved for damage-label calibration, original insured property identities, property claims or globally transferable CAT vulnerability curves.
