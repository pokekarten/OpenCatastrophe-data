<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin ALKIS: non-admitted canonical source identity and CAT4 / BLD4 provenance bridge

**Research only; read-only metadata reconciliation. No automatic model admission.**

## Two different CAT4-labelled databases, no merge of their trust domains

1. `scripts/export_cat_source_crosswalk_sqlite_v0.py` materializes the independent
   discovery/access/linkage metadata in a NEW, isolated `*.cat.sqlite` file
   (SQLite application ID `0x43415434`, profile CAT4, version 1).
   The registered exact provider is `de.berlin.alkis-gebaeude.wfs`.
   Registry candidate remains `not_admitted`, `not_reviewed` for both
   dataset rights and scientific suitability; this is not an acquisition approval.
2. `research_runners/berlin_alkis_gebaeude_five_feature_join_v0.py` stages
   one already validated, bounded official Berlin WFS sample as a different
   database (application ID `0x424C4434`, BLD4, version 1) containing at most
   five local derived polygons, no original feature IDs or addresses, and
   independent CAT1/CAT2 region attribution. The WFS is mutable, so source
   retrieval UTC/SHA are preserved. Neither database implies insured values.

## Exact read-only identity bridge

`scripts/verify_berlin_cat4_source_lineage_v0.py` requires both preexisting
databases, rejects symlinks, filename/size/profile/schema mismatch and
nonzero model authority, checks the canonical provider and URL against the
landscape JSON, and checks the BLD4 source root, layer, frozen rights label,
original WFS response SHA256 format, UTC receipt, unknown building vintage,
2021 reference boundaries, 1–5 source-derived polygons, their nonzero area,
and sole DE3 regional code.

It prints a small aggregate JSON receipt only. It does **not** read, output,
relocate or transform individual geometry records; re-download provider data;
verify source original bytes; prove that the two databases derive from an
independently authenticated immutable provider snapshot; or grant model rights.

Example after independently creating the two source-specific SQLite files:

```bash
python -m scripts.verify_berlin_cat4_source_lineage_v0 \
  --registry-cat4 /secure/cat-data/staging/source-research.cat.sqlite \
  --building-bld4 /secure/cat-data/staging/berlin-5-buildings.cat.sqlite
```

Reproduce synthetic-only tests:

```bash
python -m unittest tests.test_verify_berlin_cat4_source_lineage_v0 -v
```

The existing reviewed Berlin workflow exercises the identity bridge **after**
its one fixed original WFS response and the exact independent geography
validation, using temporary source registry and BLD4 databases only. No
additional remote provider access, automatic portfolio inference, or Neon
write is authorized by this research PR.

## Remaining scientific / rights gates

- The published provider licence is documented as
  **Datenlizenz Deutschland Zero 2.0**, but source/attribute/derivative rights
  must be separately validated for any scaled production use; a source
  candidate is explicitly `rights_review_status=not_reviewed`.
- The 2026 mutable buildings are not a 2021 building census. CAT1/CAT2
  NUTS2021 DE3 describes region matching, not per-building historical existence.
- Provider IDs and complete stock are unknown; geometry does not imply
  independent building identity, number of insured risks, TIV, occupancy,
  construction year, or loss vulnerability.
- For modeling, require exact historical release/vintage, source lineage,
  rights approval, independent overlap validation, uncertainty diagnostics
  and a separate explicit admission gate.

Official sources:
- https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a
- https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/datenbereitstellung/
- https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&service=WFS
