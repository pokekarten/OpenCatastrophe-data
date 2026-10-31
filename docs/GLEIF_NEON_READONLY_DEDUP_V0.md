<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Read-only Neon LEI de-duplication: CAT-only research v0

**No Neon writes, new companies, parents, portfolios or inferred insured exposures.**

This audit compares the six exact-source-verified Level-1 GLEIF legal-entity IDs in our dedicated CAT-only SQLite study against a small **operator-created read-only** export from Neon `insurance-risk-core`. It can only print a pending-manual-review plan. It has no PostgreSQL driver, Neon credential handling, network call or write entrypoint.

## Real read-only inspection, 31 October 2026

Observed in the physically separate Neon project `insurance-risk-core` (distinct from the Pokémon `tcgp2p-core` project): `entity.organization` 22 rows, `entity.organization_identifier` 31 rows (18 `GLEIF_LEI`, 13 `ACRA_UEN`); `entity.relationship_observation` 11 rows; `entity.organization_relationship` zero asserted parent records. Five of six exact GLEIF pilot IDs already have `is_verified=true` (Allianz SE, Hannover Rück, Munich Re, SCOR SE and SCOR GLOBAL REINSURANCE FRANCE). The remaining source-verified pilot candidate is `969500PB3BN0WIF01B32` / SCOR EUROPE SE, not currently registered under that LEI. No duplicate identifier values were observed in the existing identity table.

Seven first-party GLEIF Level-2 items are already present as research observations, not as ownership percentage or treaty relationships. `registry.entity_feed` has `feed_id=gleif_global`, `rights_status=cc0_verified` and **`automated_import_allowed=false`**. These observations are read-only, time-specific, not authorizations to modify Neon.

### Build a minimal, sanitized JSON receipt

Use only SELECT queries against Neon; no SQL here modifies tables. To list the six pilot LEIs and their verified status:

```sql
SELECT identifier_scheme, identifier_value, is_verified
FROM entity.organization_identifier
WHERE identifier_scheme = 'GLEIF_LEI'
  AND identifier_value IN (
    '529900K9B0N5BT694847', '529900KIN5BE45V5KB18',
    '529900MUF4C20K50JS49', '549300KCPG3666EE4546',
    '96950056ULJ4JI7V3752', '969500PB3BN0WIF01B32'
  )
ORDER BY identifier_value;
```

Check the feed's actual current restrictions separately:

```sql
SELECT feed_id, rights_status, automated_import_allowed
FROM registry.entity_feed
WHERE feed_id = 'gleif_global';
```

Combine only the selected columns in the following small JSON structure **outside source control**. No Neon UUIDs, customer data or credentials are needed:

```json
{
  "schema_version": "oc-gleif-neon-readonly-export-v0",
  "feed": {"feed_id": "gleif_global", "rights_status": "cc0_verified", "automated_import_allowed": false},
  "identifiers": [
    {"identifier_scheme": "GLEIF_LEI", "identifier_value": "529900K9B0N5BT694847", "is_verified": true}
  ]
}
```

The above **single identifier is an illustrative fragment**, not a complete Neon export. Do not represent that demonstration as a full matching result; supply all confirmed matching rows to the audit.

Execute against a verified local CAT-only SQLite research pilot (which must already contain six GLEIF Level-1 observations):

    python scripts/gleif_neon_readonly_identity_audit_v0.py --cat-sqlite /tmp/opencat-research.sqlite --neon-readonly-export /tmp/private-gleif-neon-readonly.json

The source SQLite opens with `mode=ro` and `PRAGMA query_only=ON`; the export must attest that automated import remains **false**. Duplicates, unverified LEIs, unexpected records, unknown database application IDs, altered source scientific role or a missing original provider SHA fail closed. Output only public LEI identifiers, raw source hashes and a missing/present tally.

## Stage gates

Use the output as a review queue, **not an import instruction**. Existing 5 verified LEIs should be reused, not inserted again. SCOR EUROPE SE requires separate registry/legal-entity matching, source rights, review and explicit import authorization before any Neon mutation. GLEIF Level-2 describes **accounting consolidation or reporting exceptions**, never beneficial ownership share, insurance treaty structure, insurer exposure or CAT catastrophe losses.

GLEIF's official terms provide LEI reference data as CC0: https://www.gleif.org/en/meta/lei-data-terms-of-use
