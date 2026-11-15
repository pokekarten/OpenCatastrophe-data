<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Monty STAC event-linkage boundary — research v0 (2026-11-03)

## Source access and rights status

The source discovery entry `ifrc.montandon.global-crisis-data-bank.api` has a
source-specific fail-closed access contract at
[`access/ifrc.montandon.global-crisis-data-bank.api.json`](../../access/ifrc.montandon.global-crisis-data-bank.api.json).
The official [Montandon getting-started instructions](https://montandondata.org/get-started.html)
say the API requires a token generated through an approved IFRC GO account
because some upstream data have licensing restrictions. The contract is
`blocked_credentials`, `document_only` and `probe_contract.mode=none`.
Neither the discovery entry, the public docs nor this research code grant rights
to automate data ingestion, retain raw bytes, redistribute material or deploy
commercial insurance products. The STAC production root is documented as
`https://montandon-eoapi.ifrc.org/stac`; Monty developer examples may use a
different **staging** host. A host/credential cannot be chosen by an untrusted
STAC item.

## Important documented correction: corr_id is source-local

The upstream [Monty correlation-algorithm guide](https://ifrcgo.org/monty-stac-extension/model/stac-api/correlation_algorithms/)
explicitly warns:

- `monty:corr_id` is **not** a global cross-provider event key;
  it can change with country, hazard normalization, centroid block and episode,
  even if two records describe the same disaster.
- `monty:src_event_id` identifies the original **source-local** disaster item,
  but multiple episodes and source providers may use the same identifier syntax.
- Monty recommends event-to-event dynamic filtering using intersecting
  hazard classifications, countries and time, optionally geometry, rather
  than equating different providers' `corr_id` values.
- A correlation **candidate** is not proved physical identity, a shared
  earthquake rupture, an insurance hours-clause occurrence or an independent
  damage benchmark.

This matters especially for the 2023 Türkiye/Syria sequence. The available
USGS catalog anchors `us6000jllz`, `us6000jlm1` and `us6000jlqa` are
**different physical earthquake catalogue entries**; even country/date/hazard
agreement does not establish one combined physical shock or treaty occurrence.
Country mismatch (for a cross-border event) and hazard-code mismatch (for
different classification taxonomies) also must not assert a proven physical
nonmatch.

## Bounded executable comparator

[`research_runners/monty_stac_event_linkage_gate_v0.py`](../../research_runners/monty_stac_event_linkage_gate_v0.py)
implements a **standalone, original, offline** metadata gate. No Monty package
code, provider assets, API requests, customer data or credentials are included.

1. A trusted caller, not the STAC item's `source` string, supplies an
   exact source namespace and a controlled `first_received_at` timestamp.
   Event time from STAC `datetime` is **not** publication/receipt time.
2. It validates one source **event** STAC Feature, issuer source ID,
   episode number, local correlation identifier, country and hazard lists,
   supported UTC time interval and optional finite 2D bbox.
   Reference, hazard and impact items do not silently become event sources.
3. An as-of knowledge cut rejects a future or missing controlled receipt
   (the sample receipt is synthetic and does not prove independent authority).
4. Same-source issuer ID and episode can be labelled a same-source alias,
   never physically verified or model admitted.
5. Cross-source country/hazard/time/bbox overlap produces only a
   `CROSS_SOURCE_CANDIDATE_REQUIRES_REVIEW` or
   `CROSS_SOURCE_CANDIDATE_SPATIAL_UNKNOWN` state, **never** an automatic
   global event identity or contractual occurrence merger.
6. Nonoverlapping evidence yields only a bounded nonmatch by the available
   observation support, not proof that the two sources cannot describe
   some larger related disaster.
7. The comparator does not normalize hazard-code ontologies; it requires
   **exact** overlap for a candidate and returns unresolved for differing
   code lists. Any UNDRR/GLIDE/EM-DAT code crosswalk needs a separate,
   published and versioned taxonomy contract.
8. Polygon/antimeridian geometry, uncertainty windows, source revision
   precedence, event split/merge and correlation transitivity are **not**
   implemented. A pairwise candidate relation is explicitly not a global
   equivalence relation; do not connect A=B and B=C into A=C.

Run without any network:

```sh
python -m unittest tests.test_monty_stac_event_linkage_gate_v0 -v
python research_runners/monty_stac_event_linkage_gate_v0.py
python scripts/check_all.py
```

The test suite challenges per-source `corr_id`, cross-source candidates,
same-source episodes, separate 2023 shock timestamps, missing/future
receipts, taxonomy/country ambiguity, nonoverlapping geographic support,
spoofed source metadata, unsupported STAC roles and malformed times/boxes.

## Next evidence before useful real integration

The source must pass three separate gates: (1) IFRC credential/terms and
source-provider rights, (2) independently pinned original STAC/version/receipt
provenance, then (3) reviewed physical/hazard/damage/scientific fit.
Only afterward should a scoped authorised STAC reader convert authenticated
event items into a versioned source-alias table.

Downstream hazard and loss engines should receive **verified physical-event
relations** with known uncertainty, not a Monty `corr_id` string or a
news-aggregator headline. No CAT calculation, actual loss, annual risk
probability, confidence-weighted global event merge or Neon write is claimed.
