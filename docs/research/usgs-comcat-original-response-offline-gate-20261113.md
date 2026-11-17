<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS ComCat — exact original-response digest and shape preflight (2026-11-13)

**This is a non-admission, no-network research gate.** The existing canonical
`access/usgs.anss.comcat.json` remains `documented_only`, with dataset/API
commercial-automation and redistribution rights **unknown**. No raw ComCat
bytes, original provider events, coordinates, insurer data or licensed partner
products are checked into this repository. Neither the access contract nor the
fixed 18-provider live-runner allowlist is changed by this work.

## Why

The earlier aggregate-only `research.usgs_comcat_origin_observation_v0`
preflight recorded **1,333 research event origins without an original response
SHA-256**; a database-record digest or copied API URL cannot close that gap.
An original response may also mutate as preferred earthquake origins,
magnitudes and products change over time. The existing product-vintage as-of
negative control is independent of, and not replaced by, this byte gate.

## Exactly what can be checked offline

`research_runners/usgs_comcat_original_response_gate_v0.py` accepts *only*
caller-supplied original bytes already acquired in an independently
authorised private environment. It never makes a request. It requires:

1. The exact frozen anonymous one-event FDSN query:
   `https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1&orderby=time&eventtype=earthquake&nodata=204`.
   **This is a proposed request identity, not an authorisation to execute it.**
2. A caller-asserted, second-precision UTC receipt time and JSON media type.
   The asserted time is **not** independent proof of historical availability.
3. At most 1 MiB of exact original response bytes; strict UTF-8 JSON,
   no duplicate object keys or non-finite numbers.
4. Exactly one GeoJSON earthquake Point feature, one matching metadata count,
   syntactically bounded event ID, timestamps and origin lon/lat/depth.
   This only validates shape, **not** completeness, magnitude quality,
   preferred origin correctness or scientifically meaningful depth.
5. A minimal summary containing the **SHA-256 of the original supplied bytes**
   and byte count, with no published feature content/event ID or model-approval
   flags. Original responses must remain outside Git and logs.

Run independent offline tests with only Python standard library:

```sh
python -m unittest tests.test_usgs_comcat_original_response_gate_v0 -v
```

The tests use entirely invented events, not a copied original ComCat payload.
A green result says nothing about a live provider response or legal access.

## Provider evidence and narrowly scoped rights conclusion

- USGS ComCat documentation describes the aggregated products of contributing
  worldwide seismic networks:
  https://www.usgs.gov/programs/earthquake-hazards/anss-comprehensive-earthquake-catalog-comcat-documentation
- The USGS ComCat FDSN event interface is documented here:
  https://earthquake.usgs.gov/fdsnws/event/1/
- The official ANSS Data and Products Policy v1.1 page, dated 2024-06-28,
  describes a policy for data and products developed by *participants*:
  https://www.usgs.gov/media/files/advanced-national-seismic-system-anss-data-and-products-policy
- USGS Data Licensing guidance distinguishes wholly federal products from
  datasets involving non-federal contributors or third-party terms:
  https://www.usgs.gov/data-management/data-licensing

**Important:** A public-domain label on the USGS policy document is not an
item-by-item reuse licence for every partner-origin ComCat response. API
availability does not establish commercial automation rights or redistribution
of all associated products. The current source remains blocked for unsupervised
provider acquisition, Git ingestion, Neon original-byte staging, CAT-model
calibration and public redistribution pending exact rights/service review.

## Next causal step

Independently review FDSN service/API terms and a product-scoped representative
response's provider attribution; if rights permit, run a single tightly bounded
original-GET in the trusted network execution plane, retain bytes and digest
privately with controlled receipt metadata, and compare the extracted event
against the 1,333 existing research observations without substituting generated
JSON or DB rows for original response bytes. Product-vintage and scientific
admission then remain separate later gates.
