<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMSR165: a second 2016 Seine/Loing flood reference, not a Paris flood-depth truth

**Reviewed 2026-11-04. Research only; no CEMS geospatial source bytes, satellite imagery, approved API probe, production data or model admission.**

## The exact primary-source finding

The [official Copernicus EMSR165 public activation](https://mapping.emergency.copernicus.eu/activations/EMSR165/) identifies an operational Rapid Mapping response to flooding in Loiret/Loing, activated **1 June 2016 at 18:45 UTC**. Its currently published metadata inventory reports **8 areas of interest (AOIs)** and **21 products**, offering delineation/monitoring maps, later grading maps, PDF representations and associated vector ZIP packages. They are **not 21 separate natural catastrophe events or 21 independent sensor observations**.

The [official report issued on 3 June 2016](https://mapping.emergency.copernicus.eu/news/copernicus-ems-rapid-mapping-activated-for-floods-in-france-germany-and-belgium/) says that **four AOIs had initially been mapped** in Seine-et-Marne/Loiret, with radar-derived flood maps since 31 May. The initial four and later eight are **different inventory dates**, not evidence of a duplicated flood. The public short activation metadata route also exposes code EMSR165, flood, France, 8 AOIs/21 products and last update 2016-06-10; an external web intermediary could read a brief response during this investigation. That is **not** a byte-authenticated or repository-authorised provider API receipt, and this PR does **not** enable API execution.

The [official CEMS Rapid Mapping data dictionary](https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/) distinguishes **event time**, **activation time**, AOI **extent**, product class **DEL/GRA**, image **acquisition UTC** and sensor, product **delivery UTC**, product **version**, data-layer provenance and download path. These are different fields with different scientific meanings. The inventory listing is insufficient to prove that any one AOI covers either Paris-Austerlitz or the Ponthierry gauge, or that a satellite scene was acquired during the river-crest interval.

## Scientific fit to our first Seine test case

| Candidate evidence | What is demonstrably present | Must not be inferred |
| --- | --- | --- |
| EMSR165 public activation | Same late-May/early-June 2016 flood context; published 8 AOIs and 21 operational products | An AOI actually contains the Paris gauge, or the entire product set is event truth |
| EMSR165 DEL | Published satellite-derived flood delineation/monitoring products | Water depth, direct river discharge, or a complete observed 2016 event footprint |
| EMSR165 GRA | Published grading products from response mapping | Surveyed asset damage, insured replacement value or insurance claims |
| EMSN028 | Separate 2016 [Risk & Recovery activation](https://mapping.emergency.copernicus.eu/activations/EMSN028/) | Same algorithm, AOI, satellite acquisition date or meaning as EMSR165 |
| 2016 Hub'Eau Seine QmnJ and HIXnJ | Earlier source-by-source station quality and original-provider value checks | A gauge height is equal to flood depth at a building |

Our [EMSN028 original FileGDB topology review](cems-emns028-filegdb-topology-audit-20261101.md) found an invalid original flood polygon and a disputed AOI-specific source/rights context. That does not automatically invalidate EMSR165; likewise, EMSR165 products do **not** cure those independent topology and rights gaps. The historical Paris stage also has instrument-failure context, and the highest Ponthierry daily mean flow was classified doubtful.

A product delivered **on 3 June** could have been imaged **before** that day. A product imaged the same UTC calendar day as the Paris peak is not automatically an observation of peak river stage, because the peak time, locality, station sampling and timezone differ. A bounding box containing the station is only a weak **necessary** geographic check; the original AOI polygon and coverage mask must still be examined.

## Access and rights scope remains intentionally unchanged

The authoritative [Copernicus EMS On-Demand Mapping terms](https://mapping.emergency.copernicus.eu/terms-and-conditions/) permit covered public product reuse, adaptation and redistribution with citation, while excluding sensitive/restricted and separately governed third-party information. These dataset-reuse rights do not automatically approve service-specific automated API execution, nor verify one ZIP's provenance.

The already reviewed [canonical CEMS Rapid Mapping access contract](../../access/copernicus.cems.rapid-mapping.public-activations.json) has status **documented_only**, API/service terms **unknown**, no authorised probe and no product-asset acquisition operation. The [existing CEMS source review](../source-reviews/copernicus-cems-on-demand-mapping.md) states these restrictions explicitly. This research does **not** modify any of those policies, fetch an original vector package or promote the historical activation to production. An older documented activation-detail route was inaccessible through a web intermediary; that alone is **not** evidence of provider outage or permission to use another route for bulk harvesting.

## Implemented and locally tested scope preflight

[The pure offline checker](../../research_runners/cems_emsr165_validation_scope_v0.py) accepts only local, size-bounded UTF-8 JSON research envelopes. It checks the frozen EMSR165 identity/country/flood semantics and 2026-11-04 public 8/21 summary. With an optional selected-product envelope, it checks an independently supplied AOI bounding box, product class, separate image acquisition and product delivery timestamps, version and optional stated file SHA-256/byte-count format. It does **not** retrieve or trust original provider bytes.

The guard **always** returns false for actual source asset authentication, API execution permission, independent observed-flood ground truth, product/third-party rights clearance, CAT model admission and insured-loss estimation. Even an exact 64-hex reported SHA string is **only an unverified format** until an authorised execution lane has independently hashed the actual original bytes.

[12 synthetic, network-free regression tests](../../tests/test_cems_emsr165_validation_scope_v0.py) passed on Linux in this research session. They test missing AOI, wrong activation or counts, geography outside Paris, grading mistaken for delineation, wrong image/delivery order, wrong/invalid dates and coordinates, fake approval flags and asserted hashes without authenticated asset bytes. Their artificial Paris-containing bbox is a **synthetic counterexample** and **does not assert any real EMSR165 AOI overlaps Paris**.

For future *separately authorised* metadata input, reproduction:

    python -m unittest discover -s tests -p 'test_cems_emsr165_validation_scope_v0.py' -v
    python research_runners/cems_emsr165_validation_scope_v0.py --metadata-json /local/reviewed-emsr165-metadata.json
    python scripts/check_all.py

## Specific next original-source test

1. Independently clear a minimal metadata API/manual acquisition route under the public repository access contract and document applicable automation rules. Do not silently treat a successful HTTP response as authorization.
2. Select **one EMSR165 DEL AOI** with a documented original AOI polygon, sensor acquisition UTC, product version/delivery and provider sensitivity/third-party conditions. Check *actual* overlap with an explicitly chosen 2016 test subarea; do not choose it from event title alone.
3. If licensed, acquire **one bounded original vector ZIP outside Git** with SHA-256 and size, unpack securely and evaluate the flood layer type, CRS, geometry topology, missing coverage and imagery quality. Prefer an acquisition close in time to a *reliably verified* flood extent/crest reference.
4. Compare the actual satellite-derived flood extent against **independent 2016 event-model results** in the same area/time. Do not treat it as building-specific flood depth, loss or a holdout if it was already used for model tuning.

**Current verdict:** EMSR165 is a promising **observed-extent validation candidate for selected Loing/Seine subareas**. It is **not yet a usable original geospatial input for Paris-Austerlitz flood-depth calibration**.
