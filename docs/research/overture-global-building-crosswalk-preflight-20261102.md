<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Overture global building crosswalk candidate preflight (2026-11-02)

## Pinned official upstream

- Publisher: Overture Maps Foundation; [official buildings guide](https://docs.overturemaps.org/guides/buildings/).
- Reviewed example release: **2026-10-21.0**, not a moving latest pointer.
- Exact original cloud prefix: https://overturemapswestus2.blob.core.windows.net/release/2026-10-21.0/theme=buildings/type=building/ (Azure); S3 bucket overturemaps-us-west-2, release/2026-10-21.0/theme=buildings/type=building/.
- [Official attribution and licensing](https://docs.overturemaps.org/attribution/): buildings theme ODbL, with source-lineage and obligations including OpenStreetMap, Esri, Microsoft and Google. Dataset availability is not permission for all derivatives; review actual source rights and commercial use per final use.
- [Official GERS reference](https://docs.overturemaps.org/gers/): a valid UUID is not proof of GERS registry membership, and building_part IDs do not carry the same GERS stability guarantee. Verification requires original registry, bridge and changelog evidence.
- Existing discovery candidate: overture.maps.buildings in landscape/sources-exposure-impact-validation.json. Do not duplicate or promote it.

## Shipped technical component

The offline script scripts/overture_building_identity_preflight_v0.py checks bounded local and Overture building polygon lists supplied as strictly structured JSON. It rejects duplicate JSON keys, nonfinite coordinates, invalid/self-intersecting polygons, impossible WGS84 coordinates, mixed release IDs, duplicate entities, UUID syntax problems, oversized batches, unexpected insurance fields and self-declared approvals.

It computes polygon intersection-over-union with fixed cutoff 0.75; **only reciprocal one-to-one pairs** become geometric *candidates*. A one-to-many or many-to-one fit is ambiguous. Any matching result remains research-only, and the output explicitly states:
- model_input_approved = false
- raw_data_import_authorized = false
- gers_registry_membership_verified = false
- geometry_crs_evidence_verified = false
- independent_validation_approved = false
- insured_value_estimated = false

Source families are caller-supplied, not independently verified. Identical OSM/Google/Microsoft-derived footprints in different products are **not** independent validation.

### Reproducible synthetic example

Save this entirely synthetic sample outside the repository as /private/synthetic-buildings.json:

    {
      "schema": "opencatastrophe-overture-building-crosswalk-preflight-v0",
      "overture_release": "2026-10-21.0",
      "geometry_crs": "EPSG:4326",
      "local_source": "synthetic-cadastre",
      "local_buildings": [
        {"local_id":"SYNTH-1","source_vintage":"2026-10-21",
         "geometry":{"type":"Polygon","coordinates":[[[10,50],[10.001,50],[10.001,50.001],[10,50.001],[10,50]]]}}
      ],
      "overture_buildings": [
        {"gers_id":"fea28f69-7afa-460c-b270-61ef74cd340c",
         "source_families":["synthetic-other"],
         "geometry":{"type":"Polygon","coordinates":[[[10,50],[10.001,50],[10.001,50.001],[10,50.001],[10,50]]]}}
      ]
    }

Run:

    python -m scripts.overture_building_identity_preflight_v0 --input /private/synthetic-buildings.json --expected-release 2026-10-21.0
    python -m unittest tests.test_overture_building_identity_preflight_v0 -v

The UUID is only an illustration, not proof of a real external building.

### Scientific and operational limits

- Polygon IoU is calculated in geographic WGS84 coordinate-plane units as a **local screening proxy**, not ellipsoidal equal-area geodetic matching. Real matches require a reviewed projected-geometry method, geodetic edge-case controls, verified CRS/source year, and manual adjudication of split/merge ambiguities.
- No source GeoParquet is downloaded by the script; no insurer portfolios, policies, insured values, loss curves, CAT runs or database writes.
- The script cannot grant licences, validate provider data provenance, establish GERS registry membership or certify an insurer-specific model.
- All inputs must come from independently legally authorized sources; never commit insurer/customer/claims or raw provider bytes to Git.

## Path to real insurer CAT models

1. Freeze an original source object identity, schema version, byte hashes and attribution/rights before a bounded cloud retrieval. Document authoritative GERS ID registry/bridge checks separately.
2. Obtain original locally applicable building polygons, vintages, use, construction materials, floor/height information and replacement-value evidence. Do not count conflated sources as distinct buildings.
3. Construct peril-specific original hazard intensities and region/peril coverage for flood, wind, earthquake, hail, wildfire, etc., with calibrated vulnerability and independent damage/claim data.
4. Keep physical building-stock estimates separate from insurer-owned or ceded exposure. Only legitimately available insurer portfolios and contractual terms can establish insurer-specific TIV, coverage and retro.
5. Ingest separately approved inputs and provenance into CAT-only Neon insurance-risk-core on a reviewed branch. Never use tcgp2p-core. Full scientific admission and native model runs remain separate gates.

This contribution introduces *code and synthetic tests only*, not a real-data acquisition or an approved CAT model.
