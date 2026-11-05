<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Netherlands BAG → 3DBAG: official building ID to modelled 3D volume

**Date:** 2026-11-05  
**Status:** Bounded original-source identity and modelled-volume research pilot only. No individual provider records/IDs or CityJSON geometry committed. No exact 3DBAG model release identified, and no right to calculate production TIV conferred.  
**Prerequisite:** merged PR #1360 (`scripts/audit_pdok_bag_wfs_private_area_v0.py`) and earlier BAG/parcel source research. **Pre-existing source candidate** `nl.tudelft.3dbag` is already in `landscape/sources-european-building-registers.json`, so this is **NOT a new independent data source**.

## Original 3DBAG technical evidence

- Official 3DBAG source documentation: https://docs.3dbag.nl/en/delivery/webservices/ . The experimental [API](https://api.3dbag.nl/api.html) allows individual `CityJSONFeature` retrieval by `NL.IMBAG.Pand.<16-digit BAG pand ID>` and the collection uses **EPSG:7415** (RD New + NAP height). Building geometries/models originate from **BAG footprints and AHN height data**; 3DBAG is a *derived* product, not independent BAG building geometry evidence.
- Original [3DBAG attribute descriptions](https://docs.3dbag.nl/en/schema/attributes/) confirm `b3_volume_lod12`, `b3_volume_lod13`, `b3_volume_lod22` in **m³**, computed by reconstruction software. `b3_val3dity_lodXX` code lists and `b3_kwaliteitsindicator` can be used as model-geometry/quality diagnostics, not as a guarantee of true measured replacement-cost volume.
- Original [download/source release listing](https://3dbag.nl/download) references v2025.09.03 and a 19GB national dump; **the tested live individual-building API responses do NOT expose a verifiable corresponding model release**. Their `metadata.version=2.0` is a **CityJSON serialisation version, NOT a 3DBAG release identifier**. Do not assume today's 3DBAG models are exactly v2025.09.03 or temporally aligned to daily updated BAG.
- The official [3DBAG terms](https://docs.3dbag.nl/en/copyright/) describe CC BY 4.0 with attribution. The original asset-level commercial/scientific rights, release pinning and insurance-use obligations are NOT yet approved in the OpenCatastrophe source manifest.

## Bounded live crosswalk receipt (only aggregates, no original identifiers)

Start with original BAG WFS projected 5-field pilot in tiny Utrecht-area window (`136701.28,455804.71,136728.86,455849.32,EPSG:28992`); **8** active `verblijfsobject` units with **767 m²** observed usable unit area and **5** distinct **single** WFS `pandidentificatie` references. Each source building ID is a **16-digit BAG pand identifier**. Those IDs were internally prefixed `NL.IMBAG.Pand.` and requested via 3DBAG's individual building API. Only in-memory aggregate research results were retained:

| Provider/quality check | Original bounded result |
| --- | ---: |
| Distinct **singular WFS pand** IDs requested at 3DBAG | **5** |
| Exact 3DBAG `CityJSONFeature.CityObjects[NL.IMBAG.Pand.ID]` matches, Building type | **5/5** |
| Building objects with `b3_kwaliteitsindicator=true` | **5/5** |
| Building objects whose LoD 1.2/1.3/2.2 `b3_val3dity_*` has no reported errors (`[]`) | **5/5** for each LoD |
| Non-null, positive `b3_volume_lod12` / `lod13` / `lod22` per building | **5/5**, **5/5**, **5/5** |
| Sum modelled building volume LoD1.2 | **4,905.03 m³** |
| Sum modelled building volume LoD1.3 | **4,508.38 m³** |
| Sum modelled building volume LoD2.2 | **4,292.96 m³** |
| Exact **model release/version** returned with the individual model | **Not verified** |

**Do not confuse three different quantities:** the 767m² BAG **unit usable area**, projected BAG/BGT **building ground footprint area**, and 3DBAG **modelled external building envelope m³** are distinct physical measures. Dividing or multiplying them without validating storeys, structural dimensions, occupancy and basement/roof definitions is unsafe. Rebuilding €/m³ guides from the private insurer are neither legally admitted nor calibrated to the specific 3DBAG LoD, so no cost or TIV has been computed.

**Provider coverage and selection warning:** 5/5 only measures the five sampled WFS singular reference IDs; it says nothing about the 21 BAG buildings in the earlier bbox, omitted/unknown multi-pand relations, other regions, new structures or nationwide 3DBAG completeness. The 3DBAG API may return HTTP 502 for an absent building; absence is not a reason to impute fabricated volume. API bounding-box pagination `numberReturned` semantics differed from the count of CityJSON feature objects in one probe; do not assume an incomplete paged response is a complete inventory.

## Implemented offline, private-only QA

`scripts/audit_3dbag_model_volume_linkage_v0.py` and `tests/test_audit_3dbag_model_volume_linkage_v0.py` use a privately obtained, WFS-filtered BAG source (verified by our existing WFS privacy/area auditor) and at most 15 original individual CityJSON source responses:

- Validate exactly the 16-digit BAG pand ID namespace; require a matching `NL.IMBAG.Pand.ID` `Building` object and EPSG:7415 CityJSON 2.0 metadata; refuse unexpected/duplicate models or WFS unit samples below the 5-record privacy gate.
- Reject invalid/nonpositive/nonfinite/over-budget model volumes, `b3_val3dity` missing code, and missing model quality flags. Exclude geometry with nonempty 3D error-code lists and quality marker `false` from approved research aggregates.
- Return **only aggregate counts and sums per LoD** if at least five distinct valid models support that LoD; suppress smaller cells. No per-building volume, address, original ID, 3D geometry or exact coordinate is output.
- Flag `exact_3dbag_release_verified=false`, `provider_response_origin_or_hash_verified=false`, `complete_multi_pand_relation_verified=false`, `source_admitted=false`, `replacement_cost_estimated=false`, `real_insured_tiv_or_policy_verified=false` regardless of a successful private test.

```sh
python -m unittest tests.test_audit_3dbag_model_volume_linkage_v0 -v
python scripts/audit_3dbag_model_volume_linkage_v0.py \
  --wfs /private/bag-wfs-five-field-bounded.json \
  --wfs-source-url '<exact approved five-field WFS GetFeature URL>' \
  --models /private/3dbag-model-01.json /private/3dbag-model-02.json /private/3dbag-model-03.json /private/3dbag-model-04.json /private/3dbag-model-05.json
python scripts/check_all.py
```

## Remaining scientific work

1. Pin the exact source release (metadata.json, original released tile/checksum) and reconcile its BAG base date with currently served WFS/GIS building statuses; licence/attribution and ongoing commercial reuse approval are separate governance decisions.
2. Compare modelled LoD1.2, LoD1.3 and LoD2.2 volumes against genuinely independent volume/height references (original LiDAR, surveyed plans, verified construction classes), not another downstream BAG-derived height guess.
3. Establish complete BAG `verblijfsobject.pand[]` relationships in a private, field-restricted extraction rather than WFS single `pandidentificatie`; preserve missing/ambiguous links and heterogeneous residential/industrial/retail/accommodation uses.
4. Only after source admission and a separately licensed building-cost baseline should any €/m³ price be applied, with scenario ranges and independently calibrated model uncertainty. A synthetic carrier portfolio needs a separate policy-penetration/market-share assignment step before gross/net AEP/OEP and inward/outward reinsurance testing.
