<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS ComCat product-vintage as-of boundary: offline research test v0

**Classification:** research/negative-control-only. This document and the executable
`research_runners/usgs_product_vintage_gate_v0.py` do **not** alter the admission
of `access/usgs.anss.comcat.json` and do not authorize an eventid/superseded query.

## Why a product revision is not a contemporaneous forecast

ComCat identifies a product version by **source + type + code + updateTime**.
The newer version supersedes an older version of the *same product*.
Different contributors and product types are not interchangeable. A product's
`updateTime` identifies its revision time; it does not prove when our
hypothetical observer had public access to those exact bytes.

The official earthquake page for the **6 February 2023 Türkiye/Syria M7.8
event, USGS `us6000jllz`**, now displays a preferred ShakeMap marked version
19 and last updated in **2025**. That is useful **later product history**,
not evidence that version 19 existed at the earthquake's first alert.
A PAGER estimate is itself model output and not an independently observed
insured loss.

- USGS product identity: https://earthquake.usgs.gov/data/catalog/products.php
- Current official event: https://earthquake.usgs.gov/earthquakes/eventpage/us6000jllz/shakemap
- Related research original-byte gap: PR #1109,
  `docs/research/usgs-comcat-origin-original-byte-gap-20261102.md` (PR head only
  until merged).

## Exact bounded offline test

```sh
python -m unittest tests.test_usgs_product_vintage_gate_v0 -v
python research_runners/usgs_product_vintage_gate_v0.py
```

The tests use only **invented** provider names, product IDs, timestamps,
hashes and receipt references. They do **not** contain source-origin bytes,
downloaded USGS products, true insurer claims or earthquake damage.

`replay_product_asof` chooses only a version with a recorded controlled
receipt **by** the knowledge cut, never on `updateTime` alone.
Its output state `CONTROLLED_RECEIPT_METADATA_ELIGIBLE` means that the
metadata relation is internally eligible for independent audit, **not** that
its receipt is externally authenticated or that it is licensed/model admitted.

A separate `retrospective_update_preview` deliberately exposes an
`updateTime`-ordered candidate but labels it **hindcast only**, with
`historical_public_availability_proven=false`. Missing receipt is not
zero loss, deleted is not an active version, and unpinned original bytes
prevent any as-of metadata-eligibility claim.

## Three distinct gates before a real event pilot

1. **Source rights / operational access:** first independently review and
   explicitly scope the canonical USGS access contract. The existing contract
   forbids arbitrary `eventid`, productcode/producttype and superseded queries,
   as well as linked asset downloads. No bypass is performed here.
2. **Original-byte and timestamp evidence:** preserve exact provider original
   bytes/hash and controlled receipt/availability evidence for each event,
   product source/type/code/updateTime, plus source/transform/version identity.
   `updateTime` or a digest alone does not prove historical availability.
   A today-downloaded 2023 revision is a *retrospective reconstruction*.
3. **Scientific/model admission:** separately qualify real ground-motion
   intensities, independent observed damage, exposure, vulnerability, financial
   terms and any probability or loss claims. Shape-valid metadata is not a
   ShakeMap footprint or a modelled insured loss. Do not turn a single event
   into AAL, OEP, AEP or SCR without a complete frequency/dependence model.

## Research result / next executable bridge

A compact synthetic counterexample deliberately delays receipt of a product
whose `updateTime` is earlier than the knowledge cut. The retrospective
selection chooses it prematurely; the controlled-receipt selection does not.
This demonstrates **an information-leakage class**, not that archived
2023 USGS availability has already been proven.

After rights, original-byte and independent availability checks,
compare the *same narrowly validated as-of product-vintage envelope* in a
separate downstream catastrophe-event lifecycle research consumer using
three clearly labelled synthetic observation cuts and portfolio scenarios.
A downstream consumer is not part of this repository's validated surface.
All source and model-readiness states remain fail-closed until then.
