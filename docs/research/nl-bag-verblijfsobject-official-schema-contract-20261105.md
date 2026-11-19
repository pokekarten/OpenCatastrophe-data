<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Dutch BAG verblijfsobject official schema contract — metadata-only evidence

**Date:** 2026-11-05  
**Status:** Original provider schema verified, no BAG verblijfsobject records retrieved or stored, no rights/science/model admission.  
**Existing programme:** merged PRs #1319 (parcel→BGT→BAG geometry) and #1347 (synthetic BAG unit-area conservations and rebuilding-cost metadata).

## Provider proof — original PDOK schema

On 2026-11-05 an uncached request to the official collection schema returned `application/schema+json`:

`https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/schema?f=json`

The original JSON Schema declares `$id=https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/schema`, `$schema=https://json-schema.org/draft/2020-12/schema`, `type=object`, title `Verblijfsobject`, and only `id` in its schema `required` array. It contains **28 described top-level properties**. Selected provider-defined fields:

| Field | Original schema semantics | Research handling |
| --- | --- | --- |
| `identificatie` | String source object identity | Transient reference, no public original ID output |
| `oppervlakte` | Integer number of unit usable m² | Not building footprint, not gross floor area or external volume |
| `pand` | **Array** of strings, `x-ogc-role=reference`, `x-ogc-collectionId=pand` | Must resolve official building references; can be multiple; never assume a direct BAG ID or a one-to-one link without a separate original identity check |
| `status` | String | Separate in-use / not-realised / lifecycle checks |
| `gebruiksdoel` | String | Keep actual purpose classification; residential-only assumptions are inadmissible |
| `postcode`, `huisnummer`, `hoofdadres_identificatie` and other address/location descriptor fields | Present in the same provider schema | **Blocked** from public research output and default exposure processing |

Public original provider collection metadata describes a verblijfsobject as a unit in **one or more buildings**. Source: https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject?f=html . The metadata does not establish the correctness of every unit's stored `pand` linkage. The API is refreshed daily; source time/version checks are mandatory.

**New script:** `scripts/audit_pdok_bag_verblijfsobject_schema_v0.py`; fully synthetic tests: `tests/test_audit_pdok_bag_verblijfsobject_schema_v0.py`. The script only reads a locally saved, original provider **schema document**, never feature rows. It fails closed on wrong official `$id`, schema version, entity type, any changed `oppervlakte` integer or `pand` reference-array semantics, missing address-field warning metadata, duplicate JSON keys and oversized documents. It emits nonidentifying contract metadata and a SHA-256 of the supplied schema bytes, not original address, building or unit IDs.

```sh
python -m unittest tests.test_audit_pdok_bag_verblijfsobject_schema_v0 -v
python scripts/audit_pdok_bag_verblijfsobject_schema_v0.py --schema /private/pdok-bag-verblijfsobject-official-schema.json
python scripts/check_all.py
```

**Original feature privacy gate:** A trial provider-side `properties=` field projection did not yield a verifiable successful source response via the research fetch channel, so selective-feature-field retrieval is **NOT VERIFIED**. Do not acquire raw address-bearing `verblijfsobject` records on that assumption. If original unit records become necessary, first establish legal data-rights scope, independently verified field projection or a privately controlled extractor which irreversibly drops blocked fields and source record IDs from external outputs, validate correct `pand` references, and keep original bytes in authorised private storage only. No user/insurer policy linkage or TIV estimation is authorised by this metadata analysis.
